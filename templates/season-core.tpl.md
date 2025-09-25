<%*
/* season-core.tpl — returns liturgical season label:
   Advent | Christmas | Epiphany | Easter
   - "Easter" covers both Lent (Ash Wed..Holy Saturday) and Eastertide (Easter..Pentecost).
   - "Epiphany" is used twice: after Jan 6 until Ash Wednesday, and from the day after Pentecost until Advent.
*/

// ---------- helpers ----------
const pad = n => String(n).padStart(2,'0');
const ymd = d => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
const addDays = (d,n)=>{const x=new Date(d); x.setDate(x.getDate()+n); return x;}
const dow = d => d.getDay(); // 0=Sun..6=Sat

function adventSunday(year){
  // 4th Sunday before Christmas (Dec 25)
  const xmas = new Date(year, 11, 25);
  const toSun = addDays(xmas, -((dow(xmas)+7-0)%7)); // Sunday on/before Dec 25
  return addDays(toSun, -21); // back 3 more weeks
}

// Western (Gregorian) Easter — Meeus/Jones/Butcher
function easterDate(year){
  const a=year%19, b=Math.floor(year/100), c=year%100;
  const d=Math.floor(b/4), e=b%4;
  const f=Math.floor((b+8)/25), g=Math.floor((b-f+1)/3);
  const h=(19*a+b-d-g+15)%30;
  const i=Math.floor(c/4), k=c%4;
  const l=(32+2*e+2*i-h-k)%7;
  const m=Math.floor((a+11*h+22*l)/451);
  const month=Math.floor((h+l-7*m+114)/31)-1; // 0=Mar
  const day=((h+l-7*m+114)%31)+1;
  return new Date(year, month, day); // Easter Sunday
}

function ashWednesday(year){
  // 46 days before Easter Sunday (40 fast days + 6 Sundays)
  return addDays(easterDate(year), -46);
}
function pentecost(year){ return addDays(easterDate(year), 49); } // 7 weeks after Easter
function epiphanyFixed(year){ return new Date(year, 0, 6); }       // Jan 6
function christmasStart(year){ return new Date(year, 11, 25); }   // Dec 25
function christmasEnd(year){ return new Date(year+1, 0, 5); }     // Jan 5 inclusive

// ---------- main API ----------
function seasonLabel(d){
  const today = d ?? new Date();

  // Anchors relevant to "today":
  // Advent that *belongs to* today's timeframe:
  const advThis = adventSunday(today.getFullYear());
  const advPrev = adventSunday(today.getFullYear()-1);
  const adventStart = (today >= advThis) ? advThis : advPrev;
  const adventNext  = adventSunday(adventStart.getFullYear()+1);

  // Christmas window spans Dec 25..Jan 5 (crosses civil year)
  const xmasStartThis = christmasStart(today.getFullYear());
  const xmasEndThis   = christmasEnd(today.getFullYear()-1); // Jan 5 of current year (for early Jan)
  const xmasStartPrev = christmasStart(today.getFullYear()-1);
  const xmasEndNext   = christmasEnd(today.getFullYear());   // Jan 5 of next year (for late Dec)

  // Easter-related anchors (based on civil year of Easter the date falls in)
  const easterThis = easterDate(today.getFullYear());
  const easterPrev = easterDate(today.getFullYear()-1);
  const easterNext = easterDate(today.getFullYear()+1);

  // Choose the Easter cycle that covers "today" around the turn of year
  // Lent/Ash Wednesday will always be in same civil year as its Easter.
  const awThis = ashWednesday(today.getFullYear());
  const penThis = pentecost(today.getFullYear());

  // ---- decision tree ----

  // 1) Advent: from Advent Sunday up to (not including) Dec 25
  if (today >= adventStart && today < christmasStart(adventStart.getFullYear())) {
    return "Advent";
  }

  // 2) Christmas: Dec 25 .. Jan 5 (inclusive)
  // Handle both late December (this year) and early January (this year’s Jan 1–5)
  if ((today >= xmasStartPrev && today <= christmasEnd(today.getFullYear()-1)) ||
      (today >= xmasStartThis && today <= xmasEndNext)) {
    return "Christmas";
  }
  // Also cover the straightforward early-January case:
  const jan5ThisYear = new Date(today.getFullYear(),0,5);
  if (today.getMonth()===0 && today.getDate()<=5) {
    return "Christmas";
  }

  // 3) Epiphany Day fixed = Jan 6; "Season after Epiphany" runs from Jan 6 up to Ash Wednesday
  const epiDay = epiphanyFixed(today.getFullYear());
  if (today >= epiDay && today < awThis) {
    return "Epiphany";
  }

  // 4) Lent & Eastertide lumped as "Easter": Ash Wednesday .. Pentecost (inclusive)
  if (today >= awThis && today <= penThis) {
    return "Easter";
  }

  // 5) After Pentecost until next Advent = (your request) label as "Epiphany"
  if (today > penThis && today < adventNext) {
    return "Epiphany";
  }

  // Fallback (shouldn’t hit): default to Epiphany
  return "Epiphany";
}

// Expose minimal API to caller
const SEASON = { seasonLabel };

tR += ""; // keep partial silent on include
%>
