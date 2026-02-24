const mineflayer = require("mineflayer");
const { mineflayer: mineflayerViewer } = require("prismarine-viewer");

const host = process.env.MC_HOST || "server";
const port = Number(process.env.MC_PORT || 25565);
const username = process.env.MC_USERNAME || "viewer-bot";
const version = process.env.MC_VERSION || false;

const viewerPort = Number(process.env.VIEWER_PORT || 3000);
const firstPerson = (process.env.VIEWER_FIRST_PERSON || "true").toLowerCase() === "true";
const viewDistance = Number(process.env.VIEWER_DISTANCE || 6);

const bot = mineflayer.createBot({
  host,
  port,
  username,
  version
});

bot.once("spawn", () => {
  mineflayerViewer(bot, {
    port: viewerPort,
    firstPerson,
    viewDistance
  });
  console.log(`viewer ready at http://localhost:${viewerPort}`);
});

bot.on("error", (err) => {
  console.error("bot error:", err);
});

bot.on("end", (reason) => {
  console.error("bot disconnected:", reason);
});
