const os = require('os');
const { mention, safeReply, escapeHtml, formatDuration } = require('../../utils/helpers');
const config = require('../../config/index');

const id = async (ctx) => {
  if (ctx.message.reply_to_message) {
    const u = ctx.message.reply_to_message.from;
    const f = ctx.message.reply_to_message.forward_from;
    let txt = `User ID: <code>${u.id}</code>`;
    if (f) txt += `\nForwarded from: <code>${f.id}</code>`;
    txt += `\nChat ID: <code>${ctx.chat.id}</code>`;
    return safeReply(ctx, txt);
  }
  await safeReply(ctx, `Your ID: <code>${ctx.from.id}</code>\nChat ID: <code>${ctx.chat.id}</code>`);
};

const info = async (ctx) => {
  const u = ctx.message.reply_to_message?.from || ctx.from;
  let role = 'Member';
  try {
    const m = await ctx.getChatMember(u.id);
    role = m.status;
  } catch {}
  const txt = `<b>User Info</b>\n` +
    `Name: ${mention(u)}\n` +
    `Username: ${u.username ? '@' + escapeHtml(u.username) : 'none'}\n` +
    `User ID: <code>${u.id}</code>\n` +
    `Language: ${escapeHtml(u.language_code || 'unknown')}\n` +
    `Role here: <b>${role}</b>`;
  await safeReply(ctx, txt);
};

const ping = async (ctx) => {
  const mongoose = require('mongoose');
  const t0 = Date.now();

  // DB ping
  let dbMs = -1;
  try {
    const ts = Date.now();
    if (mongoose.connection.readyState === 1) {
      await mongoose.connection.db.admin().ping();
      dbMs = Date.now() - ts;
    }
  } catch {}

  const apiMs = Date.now() - t0;
  const upt  = formatDuration(Math.floor(process.uptime()));
  const heap = (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(1);

  const bar = (ms) => {
    if (ms < 0)   return '⚪️ offline';
    if (ms < 100) return '🟢 excellent';
    if (ms < 250) return '🟡 good';
    if (ms < 500) return '🟠 slow';
    return '🔴 laggy';
  };

  const text =
    `<blockquote>🏓 <b>Pong!</b>\n` +
    `┏━━━━━━━━━━━━━━━━━━━━━┓\n` +
    `┃  ⚡ <b>Telegram</b>: <code>${apiMs}ms</code> ${bar(apiMs)}\n` +
    `┃  🗄 <b>MongoDB</b> : <code>${dbMs >= 0 ? dbMs + 'ms' : 'n/a'}</code> ${bar(dbMs)}\n` +
    `┃  ⏳ <b>Uptime</b>  : <b>${upt}</b>\n` +
    `┃  🧠 <b>Heap</b>    : <b>${heap} MB</b>\n` +
    `┃  🛰 <b>Node</b>    : <b>${process.version}</b>\n` +
    `┗━━━━━━━━━━━━━━━━━━━━━┛\n` +
    `🌸 <i>Hinata is awake and watching.</i></blockquote>`;

  try {
    await ctx.replyWithPhoto(
      { url: config.pingImageUrl },
      { caption: text, parse_mode: 'HTML', has_spoiler: true }
    );
  } catch {
    await safeReply(ctx, text);
  }
};

const runs = async (ctx) => {
  const replies = [
    'Yes?', 'Hmm?', 'I am here.', 'What\'s up?',
    'Ready to serve.', 'Speak, master.', 'On it.',
    'Hinata-chan reporting!', 'Reading minds is hard.',
    '👀', '✨', '🌸', '🍵',
  ];
  await ctx.reply(replies[Math.floor(Math.random() * replies.length)]);
};

const echo = async (ctx) => {
  const text = (ctx.message.text || '').split(/\s+/).slice(1).join(' ');
  if (!text) return;
  try { await ctx.deleteMessage(); } catch {}
  await ctx.reply(text);
};

const stats = async (ctx) => {
  const upt = formatDuration(Math.floor(process.uptime()));
  const mem = process.memoryUsage();
  const mb = (n) => `${(n / 1024 / 1024).toFixed(1)} MB`;
  await safeReply(ctx,
    `<b>📊 Bot Stats</b>\n` +
    `Uptime: <b>${upt}</b>\n` +
    `Heap: ${mb(mem.heapUsed)} / ${mb(mem.heapTotal)}\n` +
    `RSS: ${mb(mem.rss)}\n` +
    `Node: ${process.version}\n` +
    `Platform: ${os.platform()} ${os.arch()}\n` +
    `Hostname: ${escapeHtml(os.hostname())}`);
};

module.exports = { id, info, ping, runs, echo, stats };
