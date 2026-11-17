<!-- academy:title -->
# الذكاء الاصطناعي في الطاقة والبتروكيماويات

AI in Energy and Petrochemicals

مسار الطلاقة في البيانات والذكاء الاصطناعي · أكاديمية سدايا · USE-SEC-202 · المستوى 200

تحكم على تطبيق للذكاء الاصطناعي في الطاقة بثلاثة أسئلة: هل يغلب القاعدة البسيطة، وكم يكلف خطؤه، ومن يملك إيقافه. ثم ترتّب الحالات في خريطة تدافع عنها

يعمل المديرون والمهندسون الذين يقررون أين يكون الذكاء الاصطناعي آمنًا وجديرًا بالاستخدام على شركة طاقة متكاملة افتراضية ببيانات عامة واصطناعية. ويختبرون تنبؤًا بالأحمال مقابل خطوط الأساس، ويقدّرون تكلفة الإنذارات الكاذبة في نماذج الصيانة واكتشاف الأعطال، ويصوغون الجزء الخاص بالذكاء الاصطناعي في ملف إثبات السلامة، وينتهون بخريطة للفرص والمخاطر يدافعون عنها.

**الصيغة:** ورشة عمل: يومان من المختبرات، مع عمل تحضيري متعقَّب وخريطة تُناقَش

**صفحة المقرر:** https://sdaiaacademy.github.io/use-sec-202/
<!-- /academy:title -->

## نواتج التعلم

| | نواتج التعلم | المستوى | الدليل |
|---|---|---|---|
| LO1 | يحدد نوع كل تطبيق للذكاء الاصطناعي في الطاقة، استشاريًا أو إشرافيًا أو تحكمًا بحلقة مغلقة، والأدلة التي يحتاج إليها، استنادًا إلى عشرة تطبيقات | Awareness | جدول صحيح في ثمانية صفوف |
| LO2 | يختبر تنبؤًا متعلَّمًا بالأحمال مقابل خط الأساس الموسمي الساذج وخط أساس الاستمرارية، باستخدام تنبؤ جاهز وبيانات أحمال عامة لكل ساعة على مدى عامين | Applied | جدول أخطاء وتوصية بشأن الاستخدام |
| LO3 | يقيس زمن الإنذار المسبق والأحداث الفائتة والإنذارات الكاذبة لنماذج الصيانة واكتشاف الأعطال، ويقدّر تكلفتها، استنادًا إلى مخرجات نماذج جاهزة وبيانات عامة وجدول تكاليف | Applied | ورقة لتكلفة الأخطاء تحدد عتبة |
| LO4 | يصوغ الجزء الخاص بالذكاء الاصطناعي في ملف إثبات السلامة، بما يغطي مصادر الخطر ونطاق التشغيل والتجاوز اليدوي والبديل الاحتياطي، عند التعامل مع نظام استشاري لسلسلة ضواغط | Applied | حجة سلامة مقيَّمة بقائمة تحقق |
| LO5 | يبني خريطة للفرص والمخاطر ترتب حالات استخدام الطاقة بحسب القيمة وجاهزية البيانات ومستوى التحكم ومستوى المخاطر، في الشركة الافتراضية ذات البيانات الاصطناعية | Performance | الخريطة، وتُناقَش أمام لجنة سلامة في جلسة محاكاة |

<!-- academy:units -->
## الوحدات

| الوحدة | العنوان | الجلسات | الشرائح |
|---|---|---|---|
| اليوم 1 | هل يغلب النموذج القاعدة البسيطة، وكم يكلف خطؤه؟ | مستوى التحكم يحدد الأدلة; خط الأساس الساذج أولًا; أين يخفق التنبؤ وكم يكلف; الأعطال النادرة وثمن التنبيه | [`slides/day1.html`](slides/day1.html) |
| اليوم 2 | من الإنذار إلى حجة السلامة وخريطة الفرص | كاشف الأعطال في غرفة التحكم; حجة السلامة: من الادعاء إلى الدليل; ما حول النموذج: الأمن والبيانات والصلاحية; خريطة الفرص والمخاطر | [`slides/day2.html`](slides/day2.html) |
| المناقشة الختامية | الخريطة أمام لجنة السلامة |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## دراسة الحالة

**REPLACE: اسم الجهة الافتراضية التي تعمل عليها كل المختبرات.** REPLACE: جملتان عن دراسة الحالة وبياناتها الاصطناعية

<!-- academy:labs -->
## المختبرات

كل مختبر صفحة في `labs/` تُفتح من صفحة المقرر ومن شريحة المختبر في جلسته.

| | الجلسة | المختبر | الملف |
|---|---|---|---|
| 1.1 | اليوم 1 · الجلسة 1 | عشرة تطبيقات وثلاثة مستويات | [`D1_1_control_levels.html`](labs/D1_1_control_levels.html) |
| 1.2 | اليوم 1 · الجلسة 2 | تنبؤ المورّد أمام خطّي الأساس | [`D1_2_forecast_baselines.html`](labs/D1_2_forecast_baselines.html) |
| 1.3 | اليوم 1 · الجلسة 3 | الذروة والتكلفة وجودة السجل | [`D1_3_where_it_fails.html`](labs/D1_3_where_it_fails.html) |
| 1.4 | اليوم 1 · الجلسة 4 | تسعير أخطاء نموذج الصيانة | [`D1_4_price_maintenance.html`](labs/D1_4_price_maintenance.html) |
| 2.1 | اليوم 2 · الجلسة 1 | سجل الكاشف: التأخر والإنذارات الكاذبة | [`D2_1_detector_log.html`](labs/D2_1_detector_log.html) |
| 2.2 | اليوم 2 · الجلسة 2 | صياغة حجة السلامة لنظام «نذير» | [`D2_2_safety_argument.html`](labs/D2_2_safety_argument.html) |
| 2.3 | اليوم 2 · الجلسة 3 | فحص حجة صاغها مساعد | [`D2_3_stress_the_argument.html`](labs/D2_3_stress_the_argument.html) |
| 2.4 | اليوم 2 · الجلسة 4 | أربع حالات على الخريطة | [`D2_4_opportunity_risk_map.html`](labs/D2_4_opportunity_risk_map.html) |
<!-- /academy:labs -->

## المشروع الختامي

ثماني حالات استخدام مقيَّمة على الأقل ومشروع تجريبي واحد، تُناقَش أمام لجنة سلامة في جلسة محاكاة

**التسليم:** REPLACE: ما يسلّمه المشاركون وكيف: رابط مستودع عام، أو مجلد مشترك لمقرر بلا برمجة

## المتطلبات السابقة

- USE-FLU-103 كيف تتعلم أنظمة الذكاء الاصطناعي وأين تخفق
- يعمل في عمليات الطاقة أو يقدم المشورة لها

<!-- academy:tools -->
## الأدوات

كل سطر قدرة، والأمثلة قابلة للتبديل.

- **بيانات صناعية عامة:** بيانات C-MAPSS من NASA للمحركات التوربينية المروحية, بيانات عملية Tennessee Eastman, بيانات أحمال الشبكة المنشورة
- **التحليل دون برمجة:** Orange Data Mining, KNIME, جدول بيانات إلكتروني
<!-- /academy:tools -->

<!-- academy:sources -->
## المصادر

### المرجعيات الوطنية

- [الهيئة الوطنية للأمن السيبراني: ضوابط الأمن السيبراني للأنظمة التشغيلية (OTCC-1:2022)](https://nca.gov.sa/otcc_ar.pdf)
- [الهيئة الوطنية للأمن السيبراني: الضوابط الأساسية للأمن السيبراني](https://nca.gov.sa/ecc-ar.pdf)
- [الهيئة الوطنية للأمن السيبراني: قائمة الضوابط](https://nca.gov.sa/ar/regulatory-documents/controls-list/)
- [سدايا: مبادئ أخلاقيات الذكاء الاصطناعي](https://sdaia.gov.sa/ar/SDAIA/about/Documents/ai-principles.pdf)

### البيانات العامة المستعملة في المختبرات

- [U.S. Energy Information Administration: Hourly Electric Grid Monitor (EIA-930), about the data](https://www.eia.gov/electricity/gridmonitor/about)
- [NASA Open Data Portal: CMAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data)
- [Tennessee Eastman process simulation data, the files of the Braatz group (mirror)](https://github.com/camaramm/tennessee-eastman-profBraatz)
- [Downs and Vogel: A plant-wide industrial process control problem (1993)](https://doi.org/10.1016/0098-1354(93)80018-I)

### المنهج والأدلة

- [Hyndman and Athanasopoulos: Forecasting: Principles and Practice, 3rd edition, chapter 5 (simple methods and accuracy)](https://otexts.com/fpp3/toolbox.html)
- [Safety-Critical Systems Club: Goal Structuring Notation (GSN)](https://scsc.uk/gsn)
- [International Society of Automation: the ISA-18 series of standards on alarm management](https://www.isa.org/standards-and-publications/isa-standards/isa-18-series-of-standards)
- [International Energy Agency: Energy and AI, executive summary (2025)](https://www.iea.org/reports/energy-and-ai/executive-summary)

### الأدوات

- [Orange Data Mining](https://orangedatamining.com/)
- [KNIME Analytics Platform](https://www.knime.com/knime-analytics-platform)
<!-- /academy:sources -->

### المرجعيات الوطنية

- الضوابط الأساسية للأمن السيبراني وضوابط الأمن السيبراني للأنظمة التشغيلية الصادرة عن الهيئة الوطنية للأمن السيبراني: REPLACE: عنوان النص الرسمي
- مبادئ أخلاقيات الذكاء الاصطناعي الصادرة عن سدايا: REPLACE: عنوان النص الرسمي
- الإطار الوطني لإدارة مخاطر الذكاء الاصطناعي: REPLACE: عنوان النص الرسمي
