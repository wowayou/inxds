// check-links.js
const blc = require("broken-link-checker");
const fs = require("fs");

const results = [];
let totalLinks = 0;
let processedLinks = 0;
let brokenLinks = 0;

function printProgress() {
  const percent = totalLinks ? ((processedLinks / totalLinks) * 100).toFixed(1) : 0;
  const barLength = 20;
  const filled = Math.round((percent / 100) * barLength);
  const bar = "█".repeat(filled) + "░".repeat(barLength - filled);
  process.stdout.write(
    `\r[${bar}] ${processedLinks}/${totalLinks} checked (${brokenLinks} broken)`
  );
}

const checker = new blc.SiteChecker(
  {
    excludeExternalLinks: false
  },
  {
    link: (result) => {
      const isBroken = result.broken;
      const statusCode = result.http.response?.statusCode || null;

      results.push({
        url: result.url.resolved || result.url.original,
        broken: isBroken,
        statusCode,
        message: isBroken ? result.brokenReason || "Unknown" : "OK",
        base: result.base.resolved || ""
      });

      processedLinks++;
      if (isBroken) brokenLinks++;
      printProgress();
    },
    html: (tree, robots, response, pageUrl) => {
      totalLinks += tree.links.length;
    },
    end: () => {
      console.log("\n✅ JSON report generated: report.json");
      console.log(`🔍 Total links: ${totalLinks}`);
      console.log(`❌ Broken links: ${brokenLinks}`);
      fs.writeFileSync("report.json", JSON.stringify(results, null, 2), "utf-8");
    }
  }
);

// 本地服务器起好后检查这个入口地址
checker.enqueue("http://localhost:3000");