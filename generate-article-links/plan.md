~~链接生成工具 相应修改；~~
~~修改为自结束标签不带 / 的形式； => 添加相应的说明（这个链接工具会生成什么样规范的链接）~~

~~如果遇到 & 之类的，替换为对应的 html 实体编码 &amp;~~
~~遇到 title 中带 "", 替换为 &quot;~~
~~其他类似的~~

~~接下来~~
~~在正确转义的同时，如果是在description的content里边的这种嵌套双引号情况，还需要提醒用户也对应的修改源文件~~
~~链接生成工具的进一步优化~~

~~<a>xx&xx</a> 这里的 &必须要转义或者使用 &amp; [实体编码]~~

<div class="black_a"><a class="black_img" href="../computer/cope-with-raw-usb-drive-and-data-recovery.html"><img src="../img/computer/cope-with-raw-usb-drive-and-data-recovery/cope-with-raw-usb-drive-and-data-recovery-s.webp" loading="lazy"  alt="Cope with RAW USB Drive & Data Recovery" /></a>
      <div class="black_right">
        <h3> <a title="Cope with RAW USB Drive & Data Recovery" href="../computer/cope-with-raw-usb-drive-and-data-recovery.html">Cope with RAW USB Drive &amp; Data Recovery</a></h3>
        <p>by Achilles.H</p>
      </div>
    </div>


~~如果必须使用嵌套双引号, 替换为 `&quot;` e.g.~~
<div class="black_a"><a class="black_img" href="../computer/usb-device-not-recognized-malfunction-and-fix.html"><img src="../img/computer/usb-device-not-recognized-malfunction-and-fix/usb-device-not-recognized-malfunction-and-fix-s.webp" loading="lazy"  alt=""USB device not recognized" Malfunction And Fix" /></a>
      <div class="black_right">
        <h3> <a title=""USB device not recognized" Malfunction And Fix" href="../computer/usb-device-not-recognized-malfunction-and-fix.html">"USB device not recognized" Malfunction And Fix</a></h3>
        <p>by Achilles.H</p>
      </div>
    </div>
~~改成这种~~
<div class="black_a"><a class="black_img" href="../computer/usb-device-not-recognized-malfunction-and-fix.html"><img src="../img/computer/usb-device-not-recognized-malfunction-and-fix/usb-device-not-recognized-malfunction-and-fix-s.webp" loading="lazy"  alt="&quot;USB device not recognized&quot; Malfunction And Fix" /></a>
      <div class="black_right">
        <h3> <a title=""USB device not recognized" Malfunction And Fix" href="../computer/usb-device-not-recognized-malfunction-and-fix.html">"USB device not recognized" Malfunction And Fix</a></h3>
        <p>by Achilles.H</p>
      </div>
    </div>

~~也就是说提取的title如果是 <title>Error Fix: "Your connection is not private" in Google Chrome</title>~~
~~也要注意将 " 转换 &quot 实体编码（因为他会出现在alt属性中）~~