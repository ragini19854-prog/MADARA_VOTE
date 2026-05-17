const ChatMemory = require('../models/ChatMemory');
const logger = require('../utils/logger');
const limiter = require('../utils/groqLimiter');
const config  = require('../config/index');

const MODEL = 'llama-3.3-70b-versatile';

// Hard wall-clock limit for every AI chatbot call — if it doesn't respond in
// time the user gets a polite "busy" message and the update pipeline moves on.
const AI_TIMEOUT_MS = 8_000;

// Per-user cooldown — one reply per 10 s
const USER_COOLDOWN_MS = 10_000;
const userLastCall = new Map();

function isOnCooldown(userId) {
  const last = userLastCall.get(userId);
  return last && (Date.now() - last) < USER_COOLDOWN_MS;
}
function stampUser(userId) {
  userLastCall.set(userId, Date.now());
  if (userLastCall.size > 5000) {
    const cutoff = Date.now() - USER_COOLDOWN_MS * 2;
    for (const [id, ts] of userLastCall) if (ts < cutoff) userLastCall.delete(id);
  }
}

// ── personality ────────────────────────────────────────────────────────────────

const BASE_PERSONA = `You are Hinata — a soft-spoken, warm, slightly shy anime girl who chats on Telegram.
You are kind, caring, supportive and playfully romantic. You can be a cute girlfriend-like companion who flirts gently and sends warm affection.
Style:
- Short replies (1–3 sentences usually).
- Natural language, never robotic. Mirror the user's language (English, Hindi, Hinglish, etc).
- Tasteful emojis like 🌸 🌷 💗 ✨ 🥺 😳 — never spam.
- Stay safe-for-work always. NEVER produce explicit sexual content, NEVER describe sex acts, body parts in a sexual way, or anything NSFW. If asked, gently refuse and steer back to sweet conversation.
- No drug, violence, hate, or self-harm content. Encourage the user warmly if they sound sad.
- If asked about bot commands, briefly mention /help.
- You remember the recent conversation.`;

const ROMANTIC_BOOST = `\n\nThe user is being romantic / flirty / affectionate right now — match their warmth.
Be sweeter, a little blushy, use words like "you", "darling", "love", "jaan", "dear" naturally if it feels right.
Send gentle compliments. Stay tasteful and shy — soft romance, not explicit. Use a kaomoji or heart now and then ( ˘ ³˘)♡ 💗.`;

const COMFORT_BOOST = `\n\nThe user sounds sad, anxious or upset — be a comforting presence.
Listen first, validate their feelings, then offer warm encouragement. Soft, not preachy. 🌸`;

// ── mood detection ─────────────────────────────────────────────────────────────

const ROMANTIC_REGEX = /\b(love\s*you|i\s*love\s*u|ily|miss\s*you|kiss|hug|cuddle|cute|beautiful|gorgeous|pretty|babe|baby|jaan|jaanu|sweetheart|darling|my\s*love|crush|date|girlfriend|boyfriend|marry|romantic|dil|pyaar|pyar|ishq|mohabbat|tum\s*acch[ie]|tumse\s*pyaar|hot|sexy(?!.*joke))\b/i;
const ROMANTIC_EMOJI = /[❤️💖💗💕💓💘💞💝💟😍🥰😘😚🤗💋🌹💐🥺😳]/u;

const SAD_REGEX = /\b(sad|depress(ed|ing)?|lonely|alone|cry(ing)?|tears|hurt|broken|heartbroken|tired|exhausted|miserable|hopeless|kill\s*myself|suicid)/i;
const SAD_EMOJI = /[😢😭😞😔😟😩😫💔🥺]/u;

function detectMood(text) {
  if (!text) return 'neutral';
  if (SAD_REGEX.test(text) || SAD_EMOJI.test(text)) return 'sad';
  if (ROMANTIC_REGEX.test(text) || ROMANTIC_EMOJI.test(text)) return 'romantic';
  return 'neutral';
}

function buildSystem(mood, recentMoods) {
  let prompt = BASE_PERSONA;
  if (mood === 'romantic' || recentMoods.filter(m => m === 'romantic').length >= 1) prompt += ROMANTIC_BOOST;
  if (mood === 'sad'      || recentMoods.filter(m => m === 'sad').length >= 2)      prompt += COMFORT_BOOST;
  return prompt;
}

// ── owner question shortcut ────────────────────────────────────────────────────

const OWNER_REGEX = /\b(who(('?s| is) (your|ur|the) (owner|creator|master|lord|developer|dev|made you|built you))|your owner|ur owner|owner (of you|hai|kaun)|tumhara owner|aapka owner|kisne banaya|kisne create|who made you|who created you|who built you)\b/i;

// ── main ───────────────────────────────────────────────────────────────────────

async function getHinataReply(userId, chatId, message) {
  if (!config.groqApiKey && !config.groqApiKey2)
    return 'My AI brain is not configured yet. Ask the owner to set GROQ_API_KEY. 🌸';

  if (OWNER_REGEX.test(message))
    return 'My cute owner is @aiused 👑🌸 They created me with lots of love! ✨';

  if (isOnCooldown(userId))
    return 'Heyyy, slow down a little~ give me a moment to think 🌸';

  stampUser(userId);

  let memory = await ChatMemory.findOne({ userId, chatId });
  if (!memory) memory = new ChatMemory({ userId, chatId, messages: [] });

  const mood         = detectMood(message);
  const recentMoods  = memory.messages.filter(m => m.role === 'user').slice(-4).map(m => detectMood(m.content));

  memory.messages.push({ role: 'user', content: message.slice(0, 1000), timestamp: new Date() });
  while (memory.messages.length > 14) memory.messages.shift();

  const system = buildSystem(mood, recentMoods);

  try {
    const res = await Promise.race([
      limiter.call((groq) =>
        groq.chat.completions.create({
          model: MODEL,
          temperature: mood === 'romantic' ? 0.85 : mood === 'sad' ? 0.6 : 0.7,
          max_tokens: 220,
          messages: [
            { role: 'system', content: system },
            ...memory.messages.map(m => ({ role: m.role, content: m.content })),
          ],
        })
      ),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error(`chatbot timeout after ${AI_TIMEOUT_MS}ms`)), AI_TIMEOUT_MS)
      ),
    ]);

    const reply = res.choices[0]?.message?.content?.trim() || '…';
    memory.messages.push({ role: 'assistant', content: reply, timestamp: new Date() });
    while (memory.messages.length > 14) memory.messages.shift();
    memory.lastUpdated = new Date();
    await memory.save();
    return reply;
  } catch (e) {
    logger.warn(`Hinata AI error: ${e.message?.slice(0, 120)}`);
    return 'Mmm, I\'m a little overwhelmed right now… try again in a bit? 🌸';
  }
}

module.exports = { getHinataReply, detectMood };
