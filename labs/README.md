# الذكاء الاصطناعي في الطاقة والبتروكيماويات: المختبرات

ثمانية مختبرات لمقرر أكاديمية سدايا **USE-SEC-202**، مدة كل منها 40 دقيقة. المختبرات صفحات إرشادية بالعربية: الهدف،
والملفات، وخطوات بدقائقها وصيغ جدول بيانات تُنسخ، وأسئلة تحقق، وتمرين إضافي ✱، وملاحظات للمدرب. لا كود يكتبه المشارك،
ولا مختبر يحتاج نموذجًا لغويًّا.

كل المختبرات في جهة واحدة: **ذُرى للطاقة**، شركة طاقة متكاملة افتراضية.

## ما يحتاجه المشارك

- جدول بيانات إلكتروني يقرأ ملفات CSV بترميز UTF-8 (Excel أو Google Sheets أو LibreOffice Calc). أداة تحليل دون برمجة
  مثل Orange Data Mining أو KNIME بديل لمن يفضلها، وليست شرطًا.
- مساعد محادثة عام في المختبرات 2.2 و2.3 و2.4، اختياريًّا. لا يُرفع إليه أي ملف من جهة المشارك.
- ورقة العمل التحضيري: `files/prework_sheet.csv`.

## نقطة البداية والحل

كل مختبر يبدأ من ملفات جاهزة ولا يعتمد على مختبر آخر في اليوم نفسه. حين يبني مختبر على نتيجة سابقة، له ملف بديل في
`files/start/` يبدأ منه من لم يكمل.

| المختبر | الصفحة | يبدأ من | الحل المرجعي |
|---|---|---|---|
| 1.1 | `D1_1_control_levels.html` | `applications.csv`، `control_levels_guide.txt`، `prework_sheet.csv` | `solutions/D1_1_control_levels.md`، `solutions/applications.csv` |
| 1.2 | `D1_2_forecast_baselines.html` | `load/load_hourly.csv`، `load/vendor_brochure.txt` | `solutions/D1_2_forecast_baselines.md` |
| 1.3 | `D1_3_where_it_fails.html` | `start/forecast_errors_2024.csv`، `load/historian_export_week.csv` | `solutions/D1_3_where_it_fails.md` |
| 1.4 | `D1_4_price_maintenance.html` | `turbines/alerts_by_threshold.csv`، `turbines/cost_table.csv` | `solutions/D1_4_price_maintenance.md`، `solutions/cost_of_errors_sheet.csv` |
| 2.1 | `D2_1_detector_log.html` | `process/detector_runs.csv`، `start/cost_sheet_after_1_4.csv` | `solutions/D2_1_detector_log.md`، `solutions/cost_of_errors_sheet.csv` |
| 2.2 | `D2_2_safety_argument.html` | `safety/` | `solutions/D2_2_safety_argument.md`، `solutions/argument_reference.txt` |
| 2.3 | `D2_3_stress_the_argument.html` | `start/argument_ai_draft.txt`، `safety/` | `solutions/D2_3_stress_the_argument.md` |
| 2.4 | `D2_4_opportunity_risk_map.html` | `map/`، `start/map_four_scored.csv` | `solutions/D2_4_opportunity_risk_map.md`، `solutions/map_reference.csv` |

مفتاح المدرب ومواضع المشكلات المزروعة في `solutions/answer_key.md`، وكل الأرقام المرجعية في `solutions/key.json`.

## تشغيل الحلول

```bash
uv run labs/solutions/check.py            # كل المختبرات
uv run labs/solutions/check.py 1.3 2.1    # بعضها
```

ملف واحد يعلن اعتمادياته، ويحتاج [uv](https://docs.astral.sh/uv/). يعيد حساب كل رقم من ملفات المشاركين في `files/` بالطريقة
التي تشرحها صفحة المختبر، ويقارنه بـ`solutions/key.json`، ويطبع لكل مختبر ما حسبه و`PASS`. لا يكتب شيئًا على القرص ولا
يتصل بأي نموذج.

**ما يُشغَّل فعلًا:** كل حساب: خطّا الأساس وجدول الأخطاء، والخطأ بحسب الشهر والذروة، والتسعير غير المتماثل، وعيوب السجل
التاريخي الأربعة، وتسعير العتبات السبع، وسجل الكاشف وتسعير إعداداته، والخريطة بأعمدتها الخمسة. والمختبرات النصية تُفحص
آليًّا: مستويات التطبيقات وأدلتها، والحجة المرجعية مقابل سجلي الخطر والأدلة، والعيوب الستة في المسودة.

**ما لم يُشغَّل على نموذج:** مسودة الحجة في المختبر 2.3 كتبها مؤلف المقرر بيده بصيغة ما يكتبه مساعد. لم يُجرَّب أي أمر
على نموذج في بناء المقرر، ومسودة مساعد حقيقي ستخطئ في مواضع أخرى تكشفها قائمة التحقق نفسها.

## الملفات

| الملف | ما هو | المصدر | المزروع أو الموجود فيه |
|---|---|---|---|
| `load/load_hourly.csv` | 17,544 ساعة من الطلب وتنبؤ المشغّل، وتنبؤ المورّد لعام 2024 | عام، ونموذج دُرّب في البناء | نشرة تحسب الدقة على سنة التدريب وأمام أضعف خط أساس |
| `start/forecast_errors_2024.csv` | أعمدة المختبر 1.2 جاهزة، مع علامة الذروة | مشتق | تنبؤ ناقص في الذروة |
| `load/historian_export_week.csv` | أسبوع من أغسطس 2024 | عام، بعيوب مزروعة | قيمة مجمّدة، وأصفار، وقفزة، وساعة مكررة |
| `turbines/` | تنبيهات 40 توربينًا عند سبع عتبات، ومسارات ثلاثة | مشتق من C-MAPSS | عتبة المورّد أغلى من الأقل تكلفة |
| `process/detector_runs.csv` | 13 تشغيلة: مؤشر الانحراف وإنذارات ثلاثة إعدادات | مشتق من Tennessee Eastman | إنذار كاذب أعلى من المدّعى، وأربعة أعطال لا تُكشف |
| `safety/`، `start/argument_ai_draft.txt` | وصف «نذير» وسجلاته وقائمة التحقق، ومسودة حجة | اصطناعي | ستة عيوب في المسودة، ومرحلة ثانية «استشارية محسّنة» |
| `map/` | اثنتا عشرة حالة استخدام، ودليل التقييم | اصطناعي | قيمة مدّعاة على خط أساس ضعيف، وطاقة تغيّر درجة |
| `company_profile.txt`، `control_levels_guide.txt`، `applications.csv`، `prework_*` | الشركة، والمستويات، وعشرة تطبيقات، والعمل التحضيري | اصطناعي | أزواج النموذج الواحد بمستويين |

## إعادة توليد الملفات

```bash
uv run labs/_tools/prepare_files.py --raw <a folder outside the course>
```

يقرأ الملفات العامة الخام من المجلد المعطى، وينزّلها إليه إن غابت (نحو 190 ميغابايت)، ويدرّب النماذج الثلاثة، ويكتب
`files/` و`solutions/key.json`. لا رقم عشوائي فيه: الملفات الخام نفسها تعطي البايتات نفسها. النصوص الاصطناعية في
`_tools/case_texts.py`. الملفات الخام لا تدخل المستودع، ومن ملفات Tennessee Eastman لا يُكتب إلا المؤشر المحسوب، لأن
النسخة المنشورة لا تذكر رخصة للبيانات.
