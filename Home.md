```dataviewjs
// Today’s Torah pericope via Hebcal Leyning API
// Docs: https://www.hebcal.com/home/4277/leyning-torah-reading-api
const israel = false; // set true for Israel readings
const today = new Date();
const pad = n => String(n).padStart(2, '0');
const iso = `${today.getFullYear()}-${pad(today.getMonth()+1)}-${pad(today.getDate())}`;

const url = `https://www.hebcal.com/leyning?cfg=json&date=${iso}${israel ? "&i=on" : ""}`;

try {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();

  // Find the item that matches "today"
  const item = (data.items || []).find(it => (it.date || '').startsWith(iso));
  if (!item) {
    dv.paragraph("No Torah reading item for today (check date or API).");
  } else {
    // Name (Parashah or Holiday)
    const title = item.name?.en || "Torah Reading";
    dv.header(3, `📖 ${title}`);

    // Shabbat/holiday full kriyah?
    if (item.fullkriyah) {
      // Summary is like "Genesis 21:1-34; Numbers 29:1-6"
      if (item.summary) dv.paragraph(`**Full kriyah:** ${item.summary}`);
      if (item.haftara) dv.paragraph(`**Haftarah:** ${item.haftara}`);
    }

    // Weekday aliyot (Mon/Thu) or triennial aliyot on Shabbat
    const showAliyot = (aliyotObj, label) => {
      const nums = ["1","2","3","4","5","6","7","M","A","S"].filter(k => aliyotObj[k]);
      if (nums.length) {
        dv.paragraph(`**${label}:**`);
        const rows = nums.map(k => {
          const a = aliyotObj[k];
          return `• ${k}: ${a.k} ${a.b}–${a.e}`;
        });
        dv.list(rows);
      }
    };

    if (item.weekday) showAliyot(item.weekday, "Weekday aliyot");
    if (item.triennial) showAliyot(item.triennial, "Triennial aliyot");
    if (item.fullkriyah && !item.summary) showAliyot(item.fullkriyah, "Full kriyah aliyot");

    // Optional: Hebrew name
    if (item.name?.he) dv.paragraph(item.name.he);
  }

  // Attribution (Hebcal content is CC BY 4.0)
  dv.paragraph("Source: Hebcal Leyning API.");
} catch (e) {
  dv.paragraph(`Error fetching pericope: ${e.message || e}`);
}

```