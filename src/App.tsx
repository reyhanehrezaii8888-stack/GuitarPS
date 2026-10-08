import { useEffect, useState, type ReactNode } from "react";

type Route =
  | "login"
  | "signup"
  | "forgot"
  | "setup"
  | "home"
  | "input"
  | "searching"
  | "results"
  | "tool"
  | "explore"
  | "problems"
  | "problem-detail"
  | "profile";

type IconName =
  | "home"
  | "search"
  | "compass"
  | "bookmark"
  | "user"
  | "arrow"
  | "check"
  | "chevron"
  | "spark"
  | "clock"
  | "external"
  | "close"
  | "menu"
  | "mail"
  | "lock";

const routeTitles: Partial<Record<Route, string>> = {
  explore: "کاوش ابزارها",
  problems: "مسئله‌های من",
  profile: "پروفایل",
};

const problemText =
  "وقتی آکورد F می‌گیرم بعضی سیم‌ها صدا نمی‌دن و نمی‌فهمم کدوم سیم مشکل داره.";

const recommendations = [
  {
    name: "Chord AI",
    type: "اپلیکیشن",
    platform: "iOS · Android",
    price: "رایگان",
    badge: "بهترین تطبیق",
    need: "تشخیص دقیق صدای آکورد",
    reason:
      "صدای هر سیم را می‌شنود و کمک می‌کند بفهمی کدام نت در آکورد F واضح نیست.",
    score: "۹۶٪",
  },
  {
    name: "Fretello Chord Checker",
    type: "وب‌سایت",
    platform: "Web",
    price: "رایگان",
    badge: "ساده و سریع",
    need: "بررسی سیم‌به‌سیم آکورد",
    reason:
      "بدون نصب، آکورد را ضبط می‌کند و وضعیت هر سیم را جداگانه نشان می‌دهد.",
    score: "۹۱٪",
  },
  {
    name: "Yousician Tuner",
    type: "اپلیکیشن",
    platform: "iOS · Android",
    price: "Freemium",
    badge: "انتخاب جایگزین",
    need: "کوک و شفافیت صدا",
    reason:
      "قبل از بررسی آکورد مطمئن می‌شوی مشکل از کوک ساز نیست.",
    score: "۸۴٪",
  },
];

const recentTools = [
  { name: "Moises", need: "جداسازی گیتار از آهنگ", kind: "اپلیکیشن" },
  { name: "Chordify", need: "پیدا کردن آکورد آهنگ", kind: "وب‌سایت" },
  { name: "Soundbrenner", need: "تمرین با مترونوم", kind: "اپلیکیشن" },
];

const needs = [
  { title: "بررسی آکورد", en: "Chord checking", icon: "C" },
  { title: "پیدا کردن آکورد", en: "Chord finding", icon: "F" },
  { title: "ریتم و مترونوم", en: "Rhythm", icon: "R" },
  { title: "کوک گیتار", en: "Tuning", icon: "T" },
  { title: "تقویت گوش", en: "Ear training", icon: "E" },
  { title: "کار با آهنگ", en: "Song tools", icon: "S" },
];

const myProblems = [
  {
    title: "صدای خفه در آکورد F",
    date: "امروز",
    status: "۳ ابزار پیشنهاد شد",
    category: "آکورد",
  },
  {
    title: "پیدا کردن آکورد یک آهنگ",
    date: "۲ روز پیش",
    status: "۲ ابزار ذخیره شد",
    category: "آهنگ",
  },
  {
    title: "جا ماندن از ضرب هنگام نواختن",
    date: "هفته پیش",
    status: "۲ ابزار پیشنهاد شد",
    category: "ریتم",
  },
  {
    title: "کوک کردن گیتار در محیط شلوغ",
    date: "۱۲ خرداد",
    status: "۱ ابزار ذخیره شد",
    category: "کوک",
  },
];

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    home: <><path d="M3 11.5 12 4l9 7.5" /><path d="M5.5 10v10h13V10M9 20v-6h6v6" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    compass: <><circle cx="12" cy="12" r="9" /><path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" /></>,
    bookmark: <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-4-6 4V4.5Z" />,
    user: <><circle cx="12" cy="8" r="4" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" /></>,
    arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    spark: <><path d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3Z" /><path d="m19 15 .7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15Z" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    external: <><path d="M14 4h6v6M20 4l-9 9" /><path d="M18 13v6H5V6h6" /></>,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
    mail: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m4 7 8 6 8-6" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  };
  return (
    <svg className="icon" viewBox="0 0 24 24" width={size} height={size} fill="none" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

function Button({
  children,
  onClick,
  variant = "primary",
  className = "",
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "dark";
  className?: string;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} className={`btn btn-${variant} ${className}`} onClick={onClick}>
      {children}
    </button>
  );
}

function Field({
  label,
  placeholder,
  type = "text",
  icon,
}: {
  label: string;
  placeholder: string;
  type?: string;
  icon?: IconName;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <span className="input-wrap">
        {icon && <Icon name={icon} size={18} />}
        <input type={type} placeholder={placeholder} />
      </span>
    </label>
  );
}

function SelectField({
  label,
  options,
  compact = false,
}: {
  label: string;
  options: string[];
  compact?: boolean;
}) {
  return (
    <label className={`field ${compact ? "field-compact" : ""}`}>
      <span>{label}</span>
      <select>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </label>
  );
}

function Brand({ light = false }: { light?: boolean }) {
  return (
    <div className={`brand ${light ? "brand-light" : ""}`}>
      <span className="brand-mark"><span /><span /><span /><span /><span /><span /></span>
      <span>GuitarPS</span>
    </div>
  );
}

function Sidebar({
  route,
  go,
}: {
  route: Route;
  go: (route: Route) => void;
}) {
  const nav = [
    { route: "home" as Route, label: "خانه", icon: "home" as IconName },
    { route: "input" as Route, label: "پیدا کردن ابزار", icon: "search" as IconName },
    { route: "explore" as Route, label: "کاوش", icon: "compass" as IconName },
    { route: "problems" as Route, label: "مسئله‌های من", icon: "bookmark" as IconName },
    { route: "profile" as Route, label: "پروفایل", icon: "user" as IconName },
  ];
  return (
    <>
      <aside className="sidebar">
        <Brand />
        <nav className="side-nav">
          {nav.map((item) => (
            <Button
              key={item.route}
              variant="ghost"
              className={route === item.route ? "active" : ""}
              onClick={() => go(item.route)}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </Button>
          ))}
        </nav>
        <div className="sidebar-callout">
          <span className="mini-label">دقیق‌تر پیشنهاد بگیر</span>
          <strong>مشکلت را با جزئیات بگو.</strong>
          <Button onClick={() => go("input")} variant="dark">
            شروع جست‌وجو <Icon name="arrow" size={17} />
          </Button>
        </div>
        <Button variant="ghost" className="account-row" onClick={() => go("profile")}>
          <span className="avatar">ن</span>
          <span><strong>نیما رضایی</strong><small>Intermediate</small></span>
          <Icon name="chevron" size={16} />
        </Button>
      </aside>
      <nav className="mobile-nav">
        {nav.map((item) => (
          <Button
            key={item.route}
            variant="ghost"
            className={route === item.route ? "active" : ""}
            onClick={() => go(item.route)}
          >
            <Icon name={item.icon} />
            <span>{item.route === "input" ? "پیدا کن" : item.label}</span>
          </Button>
        ))}
      </nav>
    </>
  );
}

function Topbar({ title, go }: { title?: string; go: (route: Route) => void }) {
  return (
    <header className="topbar">
      <div className="mobile-brand"><Brand /></div>
      {title && <h1>{title}</h1>}
      <div className="top-actions">
        <Button variant="secondary" className="top-find" onClick={() => go("input")}>
          <Icon name="spark" size={17} /> پیدا کردن ابزار
        </Button>
        <Button variant="ghost" className="avatar-button" onClick={() => go("profile")}>
          <span className="avatar">ن</span>
        </Button>
      </div>
    </header>
  );
}

function AppShell({
  route,
  go,
  children,
  title,
}: {
  route: Route;
  go: (route: Route) => void;
  children: ReactNode;
  title?: string;
}) {
  return (
    <div className="app-shell">
      <Sidebar route={route} go={go} />
      <main className="main">
        <Topbar title={title} go={go} />
        {children}
      </main>
    </div>
  );
}

function SectionTitle({
  eyebrow,
  title,
  action,
  onAction,
}: {
  eyebrow?: string;
  title: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="section-title">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
      </div>
      {action && (
        <Button variant="ghost" onClick={onAction}>
          {action} <Icon name="chevron" size={17} />
        </Button>
      )}
    </div>
  );
}

function AuthPage({ mode, go }: { mode: "login" | "signup" | "forgot"; go: (r: Route) => void }) {
  const isSignup = mode === "signup";
  const isForgot = mode === "forgot";
  return (
    <div className="auth-page">
      <section className="auth-visual">
        <div className="auth-brand"><Brand light /></div>
        <div className="sound-lines" aria-hidden="true">
          {[36, 58, 82, 48, 92, 66, 42, 76, 52, 88, 62, 38].map((height, index) => (
            <span key={index} style={{ height: `${height}%` }} />
          ))}
        </div>
        <div className="auth-quote">
          <span className="eyebrow light">SMART TOOL DISCOVERY</span>
          <h2>کمتر جست‌وجو کن،<br />هوشمندانه‌تر بنواز.</h2>
          <p>نیازت را بگو؛ ابزار مناسبش را میان ده‌ها اپ و وب‌سایت پیدا می‌کنیم.</p>
        </div>
        <div className="fret-lines" aria-hidden="true" />
      </section>
      <section className="auth-form-wrap">
        <div className="auth-form">
          <div className="auth-mobile-brand"><Brand /></div>
          {isForgot ? (
            <>
              <Button variant="ghost" className="back-link" onClick={() => go("login")}>
                <Icon name="arrow" size={17} /> بازگشت
              </Button>
              <span className="auth-kicker">بازیابی حساب</span>
              <h1>رمز عبورت را فراموش کردی؟</h1>
              <p className="muted">ایمیلت را وارد کن تا لینک بازیابی برایت ارسال شود.</p>
              <Field label="ایمیل" placeholder="name@example.com" type="email" icon="mail" />
              <Button className="wide" onClick={() => go("login")}>ارسال لینک بازیابی</Button>
            </>
          ) : (
            <>
              <span className="auth-kicker">{isSignup ? "شروع کار با GuitarPS" : "خوش برگشتی"}</span>
              <h1>{isSignup ? "حساب کاربری بساز" : "وارد حساب شو"}</h1>
              <p className="muted">
                {isSignup ? "برای پیدا کردن ابزارهای متناسب با نیازت آماده‌ای؟" : "ادامه مسیرت برای پیدا کردن ابزار مناسب."}
              </p>
              <div className="auth-fields">
                {isSignup && <Field label="نام و نام خانوادگی" placeholder="مثلاً نیما رضایی" />}
                <Field label="ایمیل" placeholder="name@example.com" type="email" icon="mail" />
                <Field label="رمز عبور" placeholder="حداقل ۸ کاراکتر" type="password" icon="lock" />
              </div>
              {!isSignup && (
                <Button variant="ghost" className="forgot-link" onClick={() => go("forgot")}>
                  رمز عبور را فراموش کردم
                </Button>
              )}
              <Button className="wide" onClick={() => go(isSignup ? "setup" : "home")}>
                {isSignup ? "ساخت حساب" : "ورود به حساب"} <Icon name="arrow" size={18} />
              </Button>
              <div className="auth-switch">
                {isSignup ? "قبلاً حساب ساخته‌ای؟" : "هنوز حساب نداری؟"}
                <Button variant="ghost" onClick={() => go(isSignup ? "login" : "signup")}>
                  {isSignup ? "وارد شو" : "ثبت‌نام کن"}
                </Button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function ProfileSetup({ go }: { go: (r: Route) => void }) {
  const [level, setLevel] = useState("Intermediate");
  return (
    <div className="setup-page">
      <header><Brand /><span>مرحله ۱ از ۲</span></header>
      <div className="setup-progress"><span /></div>
      <main className="setup-card">
        <span className="auth-kicker">شخصی‌سازی پیشنهادها</span>
        <h1>کمی از نوازندگی‌ات بگو</h1>
        <p className="muted">با این اطلاعات، ابزارهایی متناسب با سطح و شرایطت پیشنهاد می‌دهیم.</p>
        <div className="setup-section">
          <label className="label-title">سطح فعلی گیتار</label>
          <div className="level-grid">
            {[
              ["Beginner", "کمتر از یک سال"],
              ["Intermediate", "۱ تا ۳ سال"],
              ["Advanced", "بیشتر از ۳ سال"],
            ].map(([title, subtitle]) => (
              <Button
                key={title}
                variant="secondary"
                className={level === title ? "selected" : ""}
                onClick={() => setLevel(title)}
              >
                <span className="radio-dot" />
                <span><strong>{title}</strong><small>{subtitle}</small></span>
              </Button>
            ))}
          </div>
        </div>
        <div className="form-grid">
          <SelectField label="چه مدت است گیتار می‌زنی؟" options={["حدود ۲ سال", "کمتر از ۶ ماه", "۶ ماه تا ۱ سال", "بیشتر از ۳ سال"]} />
          <SelectField label="زمان معمول نوازندگی در روز" options={["۳۰ تا ۴۵ دقیقه", "کمتر از ۱۵ دقیقه", "۱۵ تا ۳۰ دقیقه", "بیشتر از یک ساعت"]} />
        </div>
        <div className="setup-section">
          <label className="label-title">معمولاً در چه چیزهایی به ابزار نیاز داری؟</label>
          <div className="chip-selector">
            {["تعویض آکورد", "صدای خفه سیم‌ها", "پیدا کردن آکورد آهنگ", "ریتم", "کوک کردن", "تقویت گوش"].map((label, index) => (
              <Button key={label} variant="secondary" className={index < 3 ? "selected" : ""}>{label}</Button>
            ))}
          </div>
        </div>
        <div className="setup-actions">
          <span className="muted">بعداً از پروفایل قابل تغییر است.</span>
          <Button onClick={() => go("home")}>ذخیره و ادامه <Icon name="arrow" size={18} /></Button>
        </div>
      </main>
    </div>
  );
}

function Home({ go }: { go: (r: Route) => void }) {
  return (
    <div className="page home-page">
      <section className="hero">
        <div className="hero-copy">
          <span className="hero-pill"><Icon name="spark" size={16} /> پیشنهاد هوشمند برای نوازنده‌ها</span>
          <h1>مشکل گیتارت رو بگو،<br /><em>ابزار مناسبش</em> رو پیدا کن.</h1>
          <p>مشکل یا چیزی که می‌خوای روی گیتار باهاش کار کنی رو توضیح بده تا ابزارهای مناسب سطح و نیازت رو پیدا کنیم.</p>
          <Button onClick={() => go("input")}>پیدا کردن ابزار مناسب <Icon name="arrow" size={19} /></Button>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="art-card card-one"><span>CHORD CHECKER</span><b>F</b><i>هر سیم را دقیق بررسی کن</i></div>
          <div className="art-card card-two"><Icon name="spark" /><b>Tool match</b><span>96%</span></div>
          <div className="guitar-neck">{[1, 2, 3, 4, 5, 6].map((n) => <span key={n} />)}</div>
        </div>
      </section>

      <section className="section-block">
        <SectionTitle eyebrow="برای تو" title="ابزارهای پیشنهادی" action="مشاهده همه" onAction={() => go("results")} />
        <div className="recommended-grid">
          {recommendations.slice(0, 2).map((tool, index) => (
            <article className="tool-card" key={tool.name} onClick={() => go("tool")}>
              <div className={`tool-logo logo-${index + 1}`}>{tool.name.slice(0, 1)}</div>
              <div className="tool-card-body">
                <div className="tool-topline"><span className="match-badge">{tool.badge}</span><span className="match-score">{tool.score} تطبیق</span></div>
                <h3>{tool.name}</h3>
                <div className="meta-row"><span>{tool.type}</span><i /><span>{tool.platform}</span><i /><span>{tool.price}</span></div>
                <p>{tool.reason}</p>
                <div className="card-footer"><span className="need-tag">{tool.need}</span><Icon name="chevron" size={18} /></div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section-block">
        <SectionTitle title="کاوش بر اساس نیاز" action="همه دسته‌ها" onAction={() => go("explore")} />
        <div className="needs-grid">
          {needs.map((need) => (
            <Button key={need.title} variant="secondary" className="need-card" onClick={() => go("explore")}>
              <span className="need-icon">{need.icon}</span>
              <span><strong>{need.title}</strong><small>{need.en}</small></span>
              <Icon name="chevron" size={17} />
            </Button>
          ))}
        </div>
      </section>

      <div className="two-columns">
        <section className="section-block compact-section">
          <SectionTitle title="اخیراً دیده‌ای" action="همه" onAction={() => go("profile")} />
          <div className="list-card">
            {recentTools.map((tool, index) => (
              <Button key={tool.name} variant="ghost" className="list-row" onClick={() => go("tool")}>
                <span className={`small-logo small-logo-${index + 1}`}>{tool.name[0]}</span>
                <span><strong>{tool.name}</strong><small>{tool.need} · {tool.kind}</small></span>
                <Icon name="chevron" size={17} />
              </Button>
            ))}
          </div>
        </section>
        <section className="section-block compact-section">
          <SectionTitle title="مسئله‌های من" action="همه" onAction={() => go("problems")} />
          <div className="list-card">
            {myProblems.slice(0, 3).map((problem) => (
              <Button key={problem.title} variant="ghost" className="problem-row" onClick={() => go("problem-detail")}>
                <span className="problem-line" />
                <span><strong>{problem.title}</strong><small>{problem.date} · {problem.status}</small></span>
                <Icon name="chevron" size={17} />
              </Button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function ProblemInput({ go }: { go: (r: Route) => void }) {
  return (
    <div className="focus-page">
      <div className="focus-header">
        <span className="step-badge">۱ از ۲</span>
        <h1>با چه مشکلی در گیتار درگیری؟</h1>
        <p>همان‌طور که برای یک دوست تعریف می‌کنی بنویس؛ هرچه دقیق‌تر، پیشنهادها مرتبط‌تر.</p>
      </div>
      <div className="input-panel">
        <label className="problem-textarea">
          <span>مشکل یا نیازت را توضیح بده</span>
          <textarea defaultValue={problemText} placeholder="مثلاً: آکورد F رو می‌گیرم ولی بعضی سیم‌ها صدا نمی‌دن و نمی‌دونم مشکل از کجاست." />
          <small><Icon name="spark" size={15} /> نیازی به اصطلاحات تخصصی نیست.</small>
        </label>
        <div className="input-divider"><span>اطلاعات تکمیلی</span></div>
        <div className="form-grid three">
          <SelectField label="سطح گیتار" options={["Intermediate", "Beginner", "Advanced"]} />
          <SelectField label="نوع گیتار" options={["آکوستیک", "کلاسیک", "الکتریک", "بیس"]} />
          <SelectField label="زمان معمول نوازندگی" options={["۳۰ تا ۴۵ دقیقه", "کمتر از ۳۰ دقیقه", "بیشتر از یک ساعت"]} />
        </div>
        <div className="input-actions">
          <Button variant="ghost" onClick={() => go("home")}>انصراف</Button>
          <Button onClick={() => go("searching")}>پیدا کردن ابزارها <Icon name="spark" size={18} /></Button>
        </div>
      </div>
      <div className="privacy-note"><Icon name="lock" size={16} /> توضیحاتت فقط برای بهتر شدن همین پیشنهاد استفاده می‌شود.</div>
    </div>
  );
}

function Searching({ go }: { go: (r: Route) => void }) {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => {
      setStep((current) => {
        if (current >= 3) {
          window.clearInterval(timer);
          window.setTimeout(() => go("results"), 650);
          return 4;
        }
        return current + 1;
      });
    }, 650);
    return () => window.clearInterval(timer);
  }, [go]);
  const stages = [
    "درک مسئله شما",
    "تطبیق با سطح نوازندگی",
    "پیدا کردن ابزارهای مرتبط",
    "مقایسه بهترین گزینه‌ها",
  ];
  return (
    <div className="searching-page">
      <div className="ai-orbit"><div className="ai-core"><Icon name="spark" size={30} /></div><i /><i /><i /></div>
      <span className="auth-kicker">GUITARPS AI</span>
      <h1>در حال پیدا کردن ابزار مناسب برای تو...</h1>
      <p>نیازت را تحلیل می‌کنیم و از میان ابزارهای گیتار، مناسب‌ترین گزینه‌ها را پیدا می‌کنیم.</p>
      <div className="search-stages">
        {stages.map((label, index) => (
          <div className={`${index < step ? "done" : ""} ${index === step ? "current" : ""}`} key={label}>
            <span>{index < step ? <Icon name="check" size={16} /> : index + 1}</span>
            <strong>{label}</strong>
            {index === step && <i />}
          </div>
        ))}
      </div>
      <span className="search-hint">معمولاً کمتر از چند ثانیه زمان می‌برد</span>
    </div>
  );
}

function Results({ go }: { go: (r: Route) => void }) {
  return (
    <div className="page results-page">
      <div className="result-heading">
        <Button variant="ghost" className="back-link" onClick={() => go("input")}><Icon name="arrow" size={17} /> ویرایش نیاز</Button>
        <span className="eyebrow">نتیجه تحلیل</span>
        <h1>ابزارهای مناسب برای نیاز تو</h1>
        <p>این گزینه‌ها بر اساس توضیحت و سطح Intermediate انتخاب شده‌اند.</p>
      </div>
      <section className="your-need">
        <div className="need-spark"><Icon name="spark" size={21} /></div>
        <div><span>نیاز تو</span><strong>«می‌خواهم بفهمم چرا بعضی سیم‌ها هنگام گرفتن آکورد F صدای خفه دارند.»</strong></div>
        <Button variant="ghost" onClick={() => go("input")}>ویرایش</Button>
      </section>
      <div className="results-toolbar">
        <div><h2>ابزارهای پیشنهادی</h2><span>۳ ابزار مرتبط پیدا شد</span></div>
        <SelectField compact label="" options={["مرتب‌سازی: مرتبط‌ترین", "رایگان", "اپلیکیشن", "وب‌سایت"]} />
      </div>
      <div className="results-list">
        {recommendations.map((tool, index) => (
          <article className={`result-card ${index === 0 ? "best" : ""}`} key={tool.name}>
            {index === 0 && <span className="best-ribbon"><Icon name="spark" size={15} /> بهترین پیشنهاد برای تو</span>}
            <div className={`tool-logo logo-${index + 1}`}>{tool.name[0]}</div>
            <div className="result-main">
              <div className="tool-topline"><span className="match-score">{tool.score} تطبیق</span></div>
              <h3>{tool.name}</h3>
              <div className="meta-row"><span>{tool.type}</span><i /><span>{tool.platform}</span><i /><span>{tool.price}</span></div>
              <div className="why-box"><span>چرا این ابزار؟</span><p>{tool.reason}</p></div>
              <div className="related-line"><span>نیاز مرتبط</span><b>{tool.need}</b><span>مناسب برای</span><b>Intermediate</b></div>
            </div>
            <div className="result-actions">
              <Button variant="secondary"><Icon name="bookmark" size={18} /> ذخیره</Button>
              <Button onClick={() => go("tool")}>مشاهده ابزار <Icon name="chevron" size={17} /></Button>
              <Button variant="ghost" className="not-relevant">مرتبط نیست</Button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function ToolPage({ go }: { go: (r: Route) => void }) {
  const [saved, setSaved] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [showOpen, setShowOpen] = useState(false);
  return (
    <div className="page tool-page">
      <Button variant="ghost" className="back-link" onClick={() => go("results")}><Icon name="arrow" size={17} /> بازگشت به نتایج</Button>
      <section className="tool-header">
        <div className="tool-logo logo-1 large">C</div>
        <div className="tool-title">
          <span className="match-badge"><Icon name="spark" size={14} /> ۹۶٪ تطبیق با نیاز تو</span>
          <h1>Chord AI</h1>
          <div className="meta-row"><span>اپلیکیشن</span><i /><span>iOS · Android</span><i /><span>رایگان با خرید درون‌برنامه‌ای</span></div>
        </div>
        <div className="tool-header-actions">
          <Button variant="secondary" onClick={() => setSaved(!saved)}><Icon name="bookmark" size={18} /> {saved ? "ذخیره شد" : "ذخیره"}</Button>
          <Button onClick={() => setShowOpen(true)}>باز کردن ابزار <Icon name="external" size={18} /></Button>
        </div>
      </section>

      <div className="tool-layout">
        <main>
          <section className="content-section">
            <span className="section-number">01</span>
            <h2>این ابزار چه کاری انجام می‌دهد؟</h2>
            <p>Chord AI با شنیدن صدای گیتار، آکوردها و نت‌های در حال اجرا را تشخیص می‌دهد. می‌توانی صدای زنده ساز یا یک فایل ضبط‌شده را وارد کنی و ببینی ابزار چه نت‌هایی را می‌شنود.</p>
          </section>
          <section className="relevance-box">
            <div className="need-spark"><Icon name="spark" size={22} /></div>
            <div><span>چرا برای مسئله تو مرتبط است؟</span><p>چون گفتی هنگام گرفتن آکورد F بعضی سیم‌ها صدای واضحی ندارند، این ابزار کمک می‌کند صدای آکوردت را ثبت کنی و ببینی کدام نت تشخیص داده نمی‌شود. به این شکل می‌فهمی مشکل احتمالاً مربوط به کدام سیم است.</p></div>
          </section>
          <section className="content-section">
            <span className="section-number">02</span>
            <h2>چطور برای مشکل خودت از این ابزار استفاده کنی؟</h2>
            <p className="section-lead">این مراحل درباره استفاده از خود Chord AI است، نه یک برنامه تمرینی جدید.</p>
            <ol className="steps-list">
              {[
                ["ابزار را باز کن", "Chord AI را روی موبایل اجرا کن و دسترسی میکروفن را فعال کن."],
                ["حالت Live Chord Recognition را انتخاب کن", "در صفحه اصلی، تشخیص زنده آکورد را باز کن."],
                ["آکورد F را بنواز", "گیتار را نزدیک میکروفن بگیر و آکورد را یک‌بار واضح اجرا کن."],
                ["نت‌های تشخیص‌داده‌شده را ببین", "بررسی کن آیا همه نت‌های F، A و C نمایش داده می‌شوند یا نه."],
                ["سیم مشکل‌دار را پیدا کن", "سیم‌ها را آرام و جداگانه بزن و ببین کدام نت شناسایی نمی‌شود."],
                ["دوباره نتیجه را بررسی کن", "نحوه گرفتن همان سیم را اصلاح کن و آکورد را دوباره در ابزار امتحان کن."],
              ].map(([title, text], index) => (
                <li key={title}><span>{index + 1}</span><div><strong>{title}</strong><p>{text}</p></div></li>
              ))}
            </ol>
          </section>
          <section className="feedback-box">
            <div><span className="eyebrow">بازخورد تو</span><h2>این ابزار کمکت کرد؟</h2><p>پاسخت کمک می‌کند پیشنهادهای بعدی دقیق‌تر شوند.</p></div>
            <div className="feedback-actions">
              {[
                ["helped", "کمک کرد", "positive"],
                ["little", "کمی کمک کرد", "neutral"],
                ["no", "کمک نکرد", "negative"],
              ].map(([key, label, tone]) => (
                <Button key={key} variant="secondary" className={`${tone} ${feedback === key ? "selected" : ""}`} onClick={() => setFeedback(key)}>
                  <span className="status-dot" /> {label}
                </Button>
              ))}
            </div>
          </section>
        </main>
        <aside className="tool-aside">
          <div className="aside-card">
            <h3>قابلیت‌های ابزار</h3>
            {["تشخیص زنده آکورد", "تشخیص نت‌ها", "تحلیل فایل صوتی", "کتابخانه آکوردها", "پشتیبانی از چند ساز"].map((feature) => (
              <span className="feature-row" key={feature}><Icon name="check" size={16} />{feature}</span>
            ))}
          </div>
          <div className="aside-card">
            <h3>مناسب برای</h3>
            <div className="tag-cloud"><span>دقت آکورد</span><span>نوازنده مبتدی</span><span>خودآموزی</span><span>تشخیص نت</span></div>
          </div>
          <div className="open-card">
            <strong>آماده‌ای امتحانش کنی؟</strong>
            <p>Chord AI روی iOS و Android در دسترس است.</p>
            <Button className="wide" onClick={() => setShowOpen(true)}>باز کردن Chord AI <Icon name="external" size={18} /></Button>
            <small>لینک در پنجره جدید باز می‌شود.</small>
          </div>
        </aside>
      </div>
      {showOpen && (
        <div className="modal-backdrop" onClick={() => setShowOpen(false)}>
          <div className="open-modal" onClick={(event) => event.stopPropagation()}>
            <Button variant="ghost" className="modal-close" onClick={() => setShowOpen(false)}><Icon name="close" /></Button>
            <div className="tool-logo logo-1 large">C</div>
            <span className="eyebrow">OPEN TOOL</span>
            <h2>Chord AI را کجا باز می‌کنی؟</h2>
            <p>نسخه مناسب دستگاهت را انتخاب کن. در محصول واقعی به فروشگاه مربوط هدایت می‌شوی.</p>
            <Button className="wide" onClick={() => setShowOpen(false)}>مشاهده در App Store <Icon name="external" size={18} /></Button>
            <Button variant="secondary" className="wide" onClick={() => setShowOpen(false)}>مشاهده در Google Play <Icon name="external" size={18} /></Button>
          </div>
        </div>
      )}
    </div>
  );
}

function Explore({ go }: { go: (r: Route) => void }) {
  return (
    <div className="page">
      <section className="explore-hero">
        <span className="eyebrow">TOOL LIBRARY</span>
        <h1>ابزارها را بر اساس نیازت پیدا کن</h1>
        <p>این‌جا دسته‌بندیِ ابزارهاست؛ نه دوره آموزشی یا برنامه تمرینی.</p>
        <Button onClick={() => go("input")}>نیازت را توضیح بده <Icon name="arrow" size={18} /></Button>
      </section>
      <div className="category-grid">
        {needs.map((need, index) => (
          <article className="category-card" key={need.title}>
            <div className={`category-visual category-${index + 1}`}><span>{need.icon}</span><i /><i /><i /></div>
            <span className="eyebrow">{need.en}</span>
            <h2>{need.title}</h2>
            <p>{["بررسی شفافیت صدا و تشخیص نت‌های آکورد", "شناسایی آکوردهای یک آهنگ یا اجرای زنده", "مترونوم، تشخیص تمپو و ابزارهای همراهی", "کوک دقیق برای محیط‌های مختلف", "ابزارهای تشخیص نت و فاصله‌های صوتی", "جداسازی ساز، تغییر سرعت و لوپ بخش آهنگ"][index]}</p>
            <Button variant="ghost" onClick={() => go("results")}>مشاهده ابزارها <Icon name="chevron" size={17} /></Button>
          </article>
        ))}
      </div>
    </div>
  );
}

function Problems({ go }: { go: (r: Route) => void }) {
  return (
    <div className="page">
      <div className="page-heading-row">
        <div><span className="eyebrow">HISTORY</span><h1>مسئله‌های من</h1><p>نیازهایی که قبلاً برایشان ابزار پیدا کرده‌ای.</p></div>
        <Button onClick={() => go("input")}><Icon name="search" size={18} /> مسئله جدید</Button>
      </div>
      <div className="problem-cards">
        {myProblems.map((problem, index) => (
          <article key={problem.title} onClick={() => go("problem-detail")}>
            <span className={`problem-category color-${index + 1}`}>{problem.category}</span>
            <h2>{problem.title}</h2>
            <p>{index === 0 ? problemText : ["می‌خوام آکوردهای آهنگی که شنیدم رو بدون سرچ کردن اسمش پیدا کنم.", "وقتی همراه آهنگ می‌زنم کم‌کم از ضرب عقب می‌مونم.", "در محیط شلوغ تیونر معمولی صدای گیتارم رو درست تشخیص نمی‌ده."][index - 1]}</p>
            <footer><span><Icon name="clock" size={16} /> {problem.date}</span><strong>{problem.status}</strong><Icon name="chevron" size={18} /></footer>
          </article>
        ))}
      </div>
    </div>
  );
}

function ProblemDetail({ go }: { go: (r: Route) => void }) {
  return (
    <div className="page detail-page">
      <Button variant="ghost" className="back-link" onClick={() => go("problems")}><Icon name="arrow" size={17} /> همه مسئله‌ها</Button>
      <div className="detail-header">
        <span className="problem-category color-1">آکورد</span>
        <h1>صدای خفه در آکورد F</h1>
        <p>{problemText}</p>
        <div className="meta-row"><span>ثبت‌شده امروز</span><i /><span>سطح Intermediate</span><i /><span>گیتار آکوستیک</span></div>
      </div>
      <SectionTitle eyebrow="پیشنهادهای این مسئله" title="ابزارهای مرتبط" />
      <div className="recommended-grid">
        {recommendations.slice(0, 2).map((tool, index) => (
          <article className="tool-card" key={tool.name} onClick={() => go("tool")}>
            <div className={`tool-logo logo-${index + 1}`}>{tool.name[0]}</div>
            <div className="tool-card-body">
              <div className="tool-topline"><span className="match-score">{tool.score} تطبیق</span></div>
              <h3>{tool.name}</h3><p>{tool.reason}</p>
              <div className="card-footer"><span className="need-tag">{tool.price}</span><Icon name="chevron" size={18} /></div>
            </div>
          </article>
        ))}
      </div>
      <div className="detail-action"><div><strong>هنوز ابزار مناسب را پیدا نکرده‌ای؟</strong><span>با توضیح بیشتر، دوباره جست‌وجو کن.</span></div><Button onClick={() => go("input")}>جست‌وجوی دوباره</Button></div>
    </div>
  );
}

function Profile({ go }: { go: (r: Route) => void }) {
  return (
    <div className="page profile-page">
      <section className="profile-header">
        <div className="profile-avatar">ن<span /></div>
        <div><span className="eyebrow">YOUR PROFILE</span><h1>نیما رضایی</h1><p>nima.rezaei@example.com</p></div>
        <Button variant="secondary">ویرایش پروفایل</Button>
      </section>
      <div className="profile-grid">
        <section className="profile-card">
          <div className="card-title"><h2>اطلاعات نوازندگی</h2><Button variant="ghost">ویرایش</Button></div>
          <div className="info-grid">
            <div><span>سطح گیتار</span><strong>Intermediate</strong></div>
            <div><span>سابقه نوازندگی</span><strong>حدود ۲ سال</strong></div>
            <div><span>زمان معمول روزانه</span><strong>۳۰ تا ۴۵ دقیقه</strong></div>
            <div><span>نوع گیتار</span><strong>آکوستیک</strong></div>
          </div>
          <span className="label-title">نیازهای رایج</span>
          <div className="tag-cloud"><span>تعویض آکورد</span><span>صدای خفه سیم‌ها</span><span>پیدا کردن آکورد</span><span>ریتم</span></div>
        </section>
        <section className="profile-card saved-card">
          <div className="card-title"><h2>ابزارهای ذخیره‌شده</h2><span>۴ ابزار</span></div>
          {recentTools.map((tool, index) => (
            <Button key={tool.name} variant="ghost" className="list-row" onClick={() => go("tool")}>
              <span className={`small-logo small-logo-${index + 1}`}>{tool.name[0]}</span>
              <span><strong>{tool.name}</strong><small>{tool.kind} · {tool.need}</small></span>
              <Icon name="chevron" size={17} />
            </Button>
          ))}
        </section>
      </div>
      <section className="profile-card">
        <div className="card-title"><h2>اخیراً مشاهده‌شده</h2><Button variant="ghost">مشاهده همه</Button></div>
        <div className="recent-horizontal">
          {recentTools.map((tool, index) => (
            <Button key={tool.name} variant="secondary" onClick={() => go("tool")}>
              <span className={`small-logo small-logo-${index + 1}`}>{tool.name[0]}</span>
              <span><strong>{tool.name}</strong><small>{tool.need}</small></span>
            </Button>
          ))}
        </div>
      </section>
      <Button variant="ghost" className="logout" onClick={() => go("login")}>خروج از حساب</Button>
    </div>
  );
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => {
    const hash = window.location.hash.replace("#/", "") as Route;
    return hash || "home";
  });
  const go = (next: Route) => {
    window.location.hash = `/${next}`;
    setRoute(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  useEffect(() => {
    const onHash = () => setRoute((window.location.hash.replace("#/", "") as Route) || "home");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  if (route === "login" || route === "signup" || route === "forgot") return <AuthPage mode={route} go={go} />;
  if (route === "setup") return <ProfileSetup go={go} />;
  if (route === "searching") return <Searching go={go} />;

  const content: Partial<Record<Route, ReactNode>> = {
    home: <Home go={go} />,
    input: <ProblemInput go={go} />,
    results: <Results go={go} />,
    tool: <ToolPage go={go} />,
    explore: <Explore go={go} />,
    problems: <Problems go={go} />,
    "problem-detail": <ProblemDetail go={go} />,
    profile: <Profile go={go} />,
  };
  return <AppShell route={route} go={go} title={routeTitles[route]}>{content[route] || <Home go={go} />}</AppShell>;
}
