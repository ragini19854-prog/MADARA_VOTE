const os = require('os');
const { Markup } = require('telegraf');
const config = require('../../config/index');
const { formatDuration, escapeHtml } = require('../../utils/helpers');
const { getGroup } = require('../../utils/groupSettings');
const { ff } = require('../../utils/font');

const STICKER_SET = process.env.START_STICKER_SET || 'Koylakoyla_by_fStikBot';

const LOADING_FRAMES = [
  '✨ нℓσ вαву ✨',
  `${ff('loading')}.`,
  `${ff('loading')}..`,
  `${ff('loading')}...`,
  '🌸 нιиαтα',
  '🌸 нιиαтα χ',
  '👑 нιиαтα χ ιиfιиιту',
  '✅ ѕтαятє∂ 👑',
];

const FRAME_DELAY_MS  = 220;
const STICKER_HOLD_MS = 2000;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getFirstSticker(telegram, stickerSetName) {
  try {
    const stickerSet = await telegram.getStickerSet(stickerSetName);
    if (stickerSet && stickerSet.stickers && stickerSet.stickers.length > 0) {
      return stickerSet.stickers[0].file_id;
    }
  } catch (err) {
    console.error('[startCommand] Failed to fetch sticker set:', err.message);
  }
  return null;
}

async function playStartAnimation(ctx) {
  try {
    const fileId = await getFirstSticker(ctx.telegram, STICKER_SET);
    if (fileId) {
      const stickerMsg = await ctx.replyWithSticker(fileId);
      await sleep(STICKER_HOLD_MS);
      try { await ctx.telegram.deleteMessage(ctx.chat.id, stickerMsg.message_id); } catch {}
    }
  } catch {}

  let loadingMsg = null;
  try {
    loadingMsg = await ctx.reply(
      `<blockquote>${LOADING_FRAMES[0]}</blockquote>`,
      { parse_mode: 'HTML' },
    );
  } catch (err) {
    console.error('[startCommand] Failed to send loading message:', err.message);
    return;
  }

  for (let i = 1; i < LOADING_FRAMES.length; i++) {
    await sleep(FRAME_DELAY_MS);
    try {
      await ctx.telegram.editMessageText(
        ctx.chat.id,
        loadingMsg.message_id,
        undefined,
        `<blockquote>${LOADING_FRAMES[i]}</blockquote>`,
        { parse_mode: 'HTML' },
      );
    } catch {}
  }

  await sleep(FRAME_DELAY_MS);
  try { await ctx.telegram.deleteMessage(ctx.chat.id, loadingMsg.message_id); } catch {}
}

const startCommand = async (ctx) => {
  const username = escapeHtml(ctx.from.first_name || 'User');
  const upt      = formatDuration(Math.floor(process.uptime()));
  const mem      = process.memoryUsage();
  const heapMB   = (mem.heapUsed / 1024 / 1024).toFixed(1);

  const arg = (ctx.message?.text || '').split(/\s+/)[1];
  if (arg && arg.startsWith('rules_')) {
    const chatId = parseInt(arg.slice(6), 10);
    if (Number.isInteger(chatId) && isFinite(chatId)) {
      try {
        const g   = await getGroup(chatId);
        const txt = g.rules || 'No rules set for that chat.';
        return ctx.reply(`📜 <b>Rules</b>:\n\n${escapeHtml(txt)}`, { parse_mode: 'HTML' });
      } catch {
        return ctx.reply('⚠️ Failed to fetch rules for that chat.');
      }
    }
  }

  await playStartAnimation(ctx);

  const startMsg =
    `<blockquote>` +
    `╔══════════════════════╗\n` +
    `║  🌸  <b>нιηαтα вσт</b>  🌸  ║\n` +
    `╚══════════════════════╝\n\n` +
    `👋 нєу, <b>${username}</b>!\n` +
    `ι αɱ <b>Hinata</b> — ყσυя αℓℓ-ιη-σηє\n` +
    `🌺 Rσsє-Grα∂є Gяσυρ Mαηαɢєя 🌺\n\n` +
    `╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌\n` +
    `⚡ <b>${ff('Uptime')}</b>  : ${upt}\n` +
    `💾 <b>${ff('Memory')}</b>  : ${heapMB} MB\n` +
    `🟢 <b>${ff('Node')}</b>    : ${process.version}\n` +
    `🖥️ <b>${ff('Host')}</b>    : ${os.hostname()}\n` +
    `╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌\n` +
    `💡 υsє /help тσ sєє αℓℓ cσɱɱαη∂s\n` +
    `🌸 <b>|ρσωєяє∂ вү нιηαтα χ ιηfιηιτყ|</b>` +
    `</blockquote>`;

  const kb = Markup.inlineKeyboard([
    [
      Markup.button.url(`➕ ${ff('Add me to Group')}`, `https://t.me/${ctx.botInfo.username}?startgroup=true`),
    ],
    [
      Markup.button.callback(`📜 ${ff('Commands')}`, 'help_main'),
      Markup.button.url(`🌐 ${ff('Website')}`, 'https://gmsxabouttgaura.netlify.app/'),
    ],
    [
      Markup.button.url(`👑 ${ff('My Lord')}`, 'https://t.me/aiused'),
      Markup.button.url(`📢 ${ff('Channel')}`, 'https://t.me/+1NRRqUd1replNTM1'),
    ],
    [
      Markup.button.callback(`ℹ️ ${ff('About')}`, 'about'),
    ],
  ]);

  const photoUrl = process.env.START_IMAGE_URL || 'https://i.ibb.co/MzCcZKz/image.jpg';
  try {
    await ctx.replyWithPhoto(photoUrl, {
      caption: startMsg,
      parse_mode: 'HTML',
      has_spoiler: true,
      ...kb,
    });
  } catch (err) {
    console.error('[startCommand] Failed to send photo, falling back to text:', err.message);
    try {
      await ctx.reply(startMsg, { parse_mode: 'HTML', ...kb });
    } catch (fallbackErr) {
      console.error('[startCommand] Fallback also failed:', fallbackErr.message);
    }
  }
};

module.exports = startCommand;
