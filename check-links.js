// check-links.js
const blc = require("broken-link-checker");
const fs = require("fs");

const results = [];

const checker = new blc.SiteChecker(
  {
    excludeExternalLinks: false
  },
  {
    link: (result) => {
      results.push({
        url: result.url.resolved || result.url.original,
        broken: result.broken,
        statusCode: result.http.response?.statusCode || null,
        message: result.broken ? result.brokenReason || "Unknown" : "OK",
        base: result.base.resolved || ""
      });
    },
    end: () => {
      fs.writeFileSync("report.json", JSON.stringify(results, null, 2), "utf-8");
      console.log("✅ JSON report generated: report.json");
    }
  }
);

// 本地服务器起好后检查这个入口地址
checker.enqueue("http://localhost:3000");
