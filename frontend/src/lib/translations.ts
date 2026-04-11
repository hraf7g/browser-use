export type Language = 'en' | 'ar';

export const translations = {
  en: {
    dir: 'ltr',
    font: 'font-inter',
    nav: {
      features: 'Features',
      howItWorks: 'How it Works',
      solutions: 'Solutions',
      faq: 'FAQ',
      signIn: 'Sign In',
      getStarted: 'Get Started',
    },
    features: {
      items: [
        { title: 'Advanced Pattern Matching', desc: 'Our agents identify strategic opportunities based on your historical win patterns and core competencies.' },
        { title: 'Real-time Notification Engine', desc: 'Get notified within milliseconds of a tender being published on any government portal in the MENA region.' },
        { title: 'One-Click Analysis', desc: 'Automatically summarize complex tender documents and identify key compliance requirements instantly.' },
        { title: 'Regional Integration', desc: 'Seamlessly monitor Etimad, Dubai Government, and 50+ other official sources through a single unified interface.' },
      ]
    },
    hero: {
      badge: 'Official MENA Tender Intelligence',
      title: 'Never miss a strategic tender again.',
      subtitle: 'Tender Watch monitors official procurement sources across the MENA region. Get instant alerts and daily briefs tailored specifically to your business size.',
      ctaPrimary: 'Start Monitoring',
      ctaSecondary: 'Watch Product Demo',
    },
    problem: {
      tag: 'The Reality',
      title: 'Manual procurement tracking is failing your growth.',
      items: [
        { title: 'Lost Opportunities', desc: 'Teams miss over 30% of relevant tenders simply by checking portals a day late.' },
        { title: 'Resource Drain', desc: 'SMEs spend average 12 hours weekly manually browsing fragmented government websites.' },
        { title: 'Alert Blindness', desc: 'Generic keyword alerts create noise. You need filtered, actionable intelligence.' },
      ]
    },
    activity: {
      title: 'Live Intelligence Stream',
      subtitle: 'Our autonomous agents monitor 50+ official portals across the MENA region in real-time.',
      status: [
        'Source checked: Etimad (KSA)',
        'New tender detected: Infrastructure',
        'Profile match: Construction SME',
        'Instant alert sent via WhatsApp',
        'Daily brief delivered to 12 users',
        'Source checked: Dubai Government',
      ],
      uptime: 'Monitoring Uptime',
      pageTitle: 'Activity & Monitoring',
      pageSubtitle: 'Real-time operational transparency across all sources.',
      filters: {
        all: 'All Activity',
        sources: 'Sources',
        matches: 'Matches',
        alerts: 'Alerts',
        failures: 'Failures'
      },
      monitoringStatus: {
        healthy: 'Healthy',
        delayed: 'Delayed',
        failed: 'Failed',
        checking: 'Checking'
      },
      summaryCards: {
        totalSources: 'Total Sources',
        healthySources: 'Healthy Sources',
        delayedSources: 'Delayed / Degraded',
        failedSources: 'Failed Sources',
        latestSuccessfulCheck: 'Latest Successful Check',
        noCheckYet: 'No successful check recorded yet',
      },
      sourceMonitoring: {
        title: 'Source Monitoring',
        lastCheck: 'Last Successful Run',
        newTenders: 'New Tenders',
        success: 'Success',
        failed: 'Failed',
        unknown: 'No recent run',
        noCheckYet: 'No successful run recorded yet',
      },
      recentRuns: {
        title: 'Recent Runs',
        latest: 'Latest',
        started: 'Started',
        duration: 'Duration',
        newTenders: 'New Tenders',
        running: 'Running',
      },
      empty: {
        title: 'No activity yet',
        subtitle: 'New source checks and match events will appear here as the system runs.',
      },
      events: {
        sourceChecked: 'Source checked',
        sourceFailed: 'Source failed',
        matchCreated: 'Match created',
        instantAlertSent: 'Instant alert sent',
        dailyBriefSent: 'Daily brief sent',
      }
    },
    howItWorks: {
      title: 'How Tender Watch Works',
      steps: [
        { n: '01', t: 'Define Interests', d: 'Input your industry, region, and business size.' },
        { n: '02', t: 'Autonomous Monitoring', d: 'Our agents scan official MENA portals 24/7.' },
        { n: '03', t: 'Smart Filtering', d: 'We remove the noise and highlight high-probability matches.' },
        { n: '04', t: 'Instant Action', d: 'Receive alerts the moment a tender goes live.' }
      ]
    },
    faq: {
      title: 'Common Questions',
      q1: 'Which countries do you cover?',
      a1: 'We cover major MENA markets including Saudi Arabia (Etimad), UAE, Qatar, and expanding across the region.',
      q2: 'Is it suitable for small businesses?',
      a2: 'Yes. We specifically designed our alerts to help SMEs react as fast as large enterprises without the overhead.',
    },
    auth: {
      login: {
        title: 'Welcome back',
        subtitle: 'Sign in to monitor your tender pipeline.',
        emailLabel: 'Work Email',
        passwordLabel: 'Password',
        rememberMe: 'Remember me',
        forgotPassword: 'Forgot password?',
        submit: 'Sign In',
        noAccount: "Don't have an account?",
        signUpLink: 'Create an account',
      },
      signup: {
        title: 'Get started for free',
        subtitle: 'Join SMEs across MENA winning more tenders.',
        workEmail: 'Work Email',
        password: 'Password',
        confirmPassword: 'Confirm Password',
        submit: 'Create Account',
        hasAccount: 'Already have an account?',
        loginLink: 'Sign in instead',
        terms: 'By signing up, you agree to our Terms and Privacy Policy.',
      },
      forgot: {
        title: 'Reset password',
        subtitle: 'Enter your email and we’ll send you a link.',
        submit: 'Send Reset Link',
        back: 'Back to login',
        success: 'Check your email for instructions.',
      },
      reset: {
        title: 'Set new password',
        subtitle: 'Choose a strong password for your account.',
        submit: 'Update Password',
        success: 'Password updated successfully.',
      },
      brand: {
        title: 'MENA’s most trusted tender intelligence.',
        benefit1: 'Real-time alerts from 50+ official sources.',
        benefit2: 'Bilingual intelligence (Arabic & English).',
        benefit3: 'Engineered for SME speed and efficiency.',
      }
    },
    app: {
      nav: {
        dashboard: 'Dashboard',
        tenders: 'Tenders',
        matches: 'Matches',
        alerts: 'Alerts',
        sources: 'Sources',
        activity: 'Activity',
        settings: 'Settings',
        account: 'Account',
        logout: 'Log Out',
      },
      session: {
        verifying: 'Verifying your session...',
        signedInAs: 'Signed in as',
      },
      topbar: {
        search: 'Search tenders, sources, or matches...',
        notifications: 'Notifications',
      },
      preview: {
        stats: {
          active: 'Active Tenders',
          matched: 'New Matches',
          sources: 'Monitored Sources',
        },
        activityTitle: 'Live Activity',
        status: {
          sourceChecked: 'Source checked',
          tenderDetected: 'New tender detected',
          matchCreated: 'Match created',
          alertSent: 'Instant alert sent',
          briefDelivered: 'Daily brief delivered',
        }
      }
    },
    dashboard: {
      hero: {
        greeting: 'Good morning, Sarah',
        summary: 'We found {n} new tenders matching your profile today.',
        actions: {
          browse: 'Browse Tenders',
          profile: 'Edit Profile'
        }
      },
      stats: {
        newMatches: 'New Matches',
        closingSoon: 'Closing Soon',
        alertsSent: 'Alerts Sent',
        sources: 'Active Sources'
      },
      priority: {
        title: 'Priority Tenders',
        viewAll: 'View All',
        matchScore: '{n}% Match',
        daysLeft: '{n} days left',
        newLabel: 'New'
      },
      activity: {
        title: 'Live Activity',
        filterAll: 'All',
        filterSources: 'Sources',
        filterMatches: 'Matches',
        status: {
          check: 'Source checked: {name}',
          detect: 'New tender detected in {name}',
          match: 'Match created for {keyword}',
          alert: 'Instant alert sent via WhatsApp',
          brief: 'Daily brief delivered'
        }
      },
      sourceHealth: {
        title: 'Source Monitoring',
        active: 'Active',
        delayed: 'Delayed',
        lastCheck: 'Last check: {time} ago'
      }
    },
    tenders: {
      title: 'Discover Tenders',
      subtitle: 'Browse and filter high-value opportunities across MENA.',
      searchPlaceholder: 'Search by title, entity, or reference...',
      resultsCount: '{n} tenders found',
      filters: {
        title: 'Filters',
        source: 'Source',
        status: 'Status',
        closing: 'Closing Window',
        category: 'Category',
        matchOnly: 'Matched only',
        newOnly: 'New only',
        reset: 'Reset All'
      },
      sort: {
        relevance: 'Most Relevant',
        newest: 'Newest',
        closingSoon: 'Closing Soon'
      },
      card: {
        viewDetails: 'View Details',
        matchReason: 'Matched for:',
        daysLeft: '{n} days left',
        closed: 'Closed'
      },
      empty: {
        title: 'No tenders found',
        description: 'Try adjusting your filters or search keywords.',
        resetAction: 'Clear all filters'
      }
    },
    details: {
      back: 'Back to Tenders',
      actions: {
        official: 'View Official Tender',
        save: 'Save for later',
        share: 'Share',
      },
      labels: {
        entity: 'Issuing Entity',
        source: 'Official Source',
        closingDate: 'Closing Date',
        openingDate: 'Opening Date',
        publishedDate: 'Published Date',
        reference: 'Tender Reference',
        category: 'Category',
        urgency: 'Urgency',
        notAvailable: 'Not available',
      },
      match: {
        title: 'Why it matches',
        reason: 'This tender matches your business interests in {keywords}.',
        confidence: '98% relevance based on your profile.',
        noKeywords: 'No matched keywords were recorded for this tender yet.',
      },
      notifications: {
        title: 'Delivery Status',
        whatsapp: 'Instant WhatsApp Alert',
        email: 'Email Brief',
        sent: 'Sent',
        notSent: 'Scheduled',
        time: 'Delivered at {time}',
        matchedAt: 'Matched at {time}',
        pending: 'No notifications have been sent yet.',
      },
      timeline: {
        title: 'Event History',
        sourceChecked: 'Source portal monitored',
        detected: 'Tender detected & normalized',
        matched: 'Profile match confirmed',
        alerted: 'Alert dispatched to team',
        briefed: 'Daily brief delivered',
        noEvents: 'No activity timeline is available yet.',
      },
      summaryUnavailable: 'No AI summary is available yet.',
      sourceLink: 'Open source link',
    },
    notifications: {
      title: 'Notifications',
      subtitle: 'Manage how and when you receive tender intelligence.',
      summary: 'Monitoring 50+ sources with instant alerts enabled.',
      tabs: {
        center: 'Notification Center',
        preferences: 'Preferences',
        history: 'Delivery History'
      },
      preferences: {
        channels: 'Channels',
        types: 'Delivery Types',
        language: 'Notification Language',
        email: 'Email Notifications',
        whatsapp: 'WhatsApp Alerts',
        whatsappDesc: 'Real-time alerts sent to your phone.',
        instant: 'Instant Alerts',
        instantDesc: 'Sent the moment a tender matches your profile.',
        daily: 'Daily Brief',
        dailyDesc: 'A morning summary of all new opportunities.',
        langAuto: 'Auto (System Language)',
        save: 'Save Changes'
      },
      history: {
        type: 'Type',
        status: 'Status',
        time: 'Time',
        matches: 'Matches',
        sent: 'Delivered',
        failed: 'Failed',
        pending: 'Pending'
      }
    },
    offers: {
      title: 'Precision intelligence for every stage.',
      subtitle: 'Choose the platform level that aligns with your operational scale.',
      plans: [
        { name: 'Freelance', price: 'Free', features: ['3 Daily Alerts', 'Email notifications', 'Single keyword profile'] },
        { name: 'SME Elite', price: '$49/mo', features: ['Unlimited Alerts', 'WhatsApp Integration', '3 Keyword Profiles', 'Market Analytics'] },
        { name: 'Enterprise', price: 'Custom', features: ['Real-time Streaming', 'API Access', 'Dedicated Account Manager', 'Legal Compliance Review'] }
      ]
    },
    smeEnterprise: {
      sme: {
        title: 'Built for SMEs',
        desc: 'Level the playing field. Get the same intelligence as global firms at a fraction of the cost.'
      },
      enterprise: {
        title: 'Enterprise Ready',
        desc: 'High-volume monitoring with robust API integrations and custom security protocols.'
      }
    },
    trust: {
      title: 'Trusted by businesses across the region.',
      subtitle: 'From local startups to multinational consultants.'
    },
    finalCta: {
      title: 'Ready to secure your next major contract?',
      desc: 'Join 2,000+ businesses who never miss a beat.',
      button: 'Create Free Account'
    },
    footer: {
      copyright: '© 2026 UAE Tender Watch. All rights reserved.',
      links: ['Privacy', 'Terms', 'Contact']
    }
  },
  ar: {
    dir: 'rtl',
    font: 'font-ibm-plex',
    nav: {
      features: 'المميزات',
      howItWorks: 'كيف يعمل',
      solutions: 'الحلول',
      faq: 'الأسئلة الشائعة',
      signIn: 'تسجيل الدخول',
      getStarted: 'ابدأ الآن',
    },
    features: {
      items: [
        { title: 'مطابقة الأنماط المتقدمة', desc: 'تحدد أدواتنا الفرص الاستراتيجية بناءً على أنماط فوزك السابقة وكفاءاتك الأساسية.' },
        { title: 'محرك تنبيهات لحظي', desc: 'احصل على تنبيه خلال أجزاء من الثانية من نشر المناقصة على أي بوابة حكومية في المنطقة.' },
        { title: 'تحليل بضغطة واحدة', desc: 'قم بتلخيص مستندات المناقصات المعقدة وتحديد متطلبات الامتثال الرئيسية فوراً.' },
        { title: 'تكامل إقليمي', desc: 'راقب منصة اعتماد وحكومة دبي وأكثر من ٥٠ مصدراً رسمياً آخر من خلال واجهة موحدة.' },
      ]
    },
    hero: {
      badge: 'ذكاء العطاءات الرسمي في الشرق الأوسط',
      title: 'لا تفوت أي مناقصة استراتيجية بعد الآن.',
      subtitle: 'يقوم "تندر ووتش" بمراقبة مصادر المشتريات الرسمية في منطقة الشرق الأوسط. احصل على تنبيهات فورية وملخصات يومية مخصصة لحجم عملك.',
      ctaPrimary: 'ابدأ المراقبة',
      ctaSecondary: 'عرض توضيحي',
    },
    problem: {
      tag: 'الواقع الحالي',
      title: 'المتابعة اليدوية للمشتريات تعيق نموك.',
      items: [
        { title: 'فرص ضائعة', desc: 'تفقد الشركات أكثر من 30٪ من المناقصات لمجرد فحص البوابات متأخراً بيوم واحد.' },
        { title: 'استنزاف الموارد', desc: 'تقضي الشركات الصغيرة والمتوسطة 12 ساعة أسبوعياً في تصفح المواقع الحكومية يدوياً.' },
        { title: 'تشتت التنبيهات', desc: 'التنبيهات العشوائية تسبب الضجيج. أنت بحاجة إلى معلومات مصفاة وقابلة للتنفيذ.' },
      ]
    },
    activity: {
      title: 'بث المعلومات المباشر',
      subtitle: 'يقوم عملاؤنا المستقلون بمراقبة أكثر من ٥٠ بوابة رسمية في جميع أنحاء المنطقة في الوقت الفعلي.',
      status: [
        'تم فحص المصدر: منصة اعتماد (السعودية)',
        'اكتشاف مناقصة جديدة: البنية التحتية',
        'تطابق الملف الشخصي: شركة مقاولات',
        'تم إرسال تنبيه عبر الواتساب',
        'تم تسليم الملخص لـ ١٢ مستخدماً',
        'تم فحص المصدر: حكومة دبي',
      ],
      uptime: 'وقت التشغيل',
      pageTitle: 'النشاط والمراقبة',
      pageSubtitle: 'شفافية تشغيلية فورية عبر جميع المصادر.',
      filters: {
        all: 'كل الأنشطة',
        sources: 'المصادر',
        matches: 'المطابقات',
        alerts: 'التنبيهات',
        failures: 'الإخفاقات'
      },
      monitoringStatus: {
        healthy: 'سليم',
        delayed: 'متأخر',
        failed: 'فاشل',
        checking: 'جاري الفحص'
      },
      summaryCards: {
        totalSources: 'إجمالي المصادر',
        healthySources: 'المصادر السليمة',
        delayedSources: 'المتأخرة / المتدهورة',
        failedSources: 'المصادر الفاشلة',
        latestSuccessfulCheck: 'آخر فحص ناجح',
        noCheckYet: 'لم يتم تسجيل فحص ناجح بعد',
      },
      sourceMonitoring: {
        title: 'مراقبة المصادر',
        lastCheck: 'آخر تشغيل ناجح',
        newTenders: 'مناقصات جديدة',
        success: 'نجاح',
        failed: 'فشل',
        unknown: 'لا يوجد تشغيل حديث',
        noCheckYet: 'لم يتم تسجيل تشغيل ناجح بعد',
      },
      recentRuns: {
        title: 'التشغيلات الأخيرة',
        latest: 'الأحدث',
        started: 'بدأ',
        duration: 'المدة',
        newTenders: 'مناقصات جديدة',
        running: 'جارٍ التشغيل',
      },
      empty: {
        title: 'لا يوجد نشاط بعد',
        subtitle: 'ستظهر عمليات فحص المصادر والأحداث المطابقة هنا أثناء تشغيل النظام.',
      },
      events: {
        sourceChecked: 'تم فحص المصدر',
        sourceFailed: 'فشل فحص المصدر',
        matchCreated: 'تم إنشاء مطابقة',
        instantAlertSent: 'تم إرسال تنبيه فوري',
        dailyBriefSent: 'تم إرسال الملخص اليومي',
      }
    },
    howItWorks: {
      title: 'كيف يعمل تندر ووتش',
      steps: [
        { n: '٠١', t: 'حدد اهتماماتك', d: 'أدخل مجال عملك، منطقتك، وحجم شركتك.' },
        { n: '٠٢', t: 'مراقبة ذاتية', d: 'عملاؤنا يمسحون البوابات الرسمية على مدار الساعة.' },
        { n: '٠٣', t: 'تصفية ذكية', d: 'نزيل الضجيج ونبرز الفرص الأكثر مطابقة لملفك.' },
        { n: '٠٤', t: 'إجراء فوري', d: 'احصل على تنبيهات فور طرح المناقصة مباشرة.' }
      ]
    },
    faq: {
      title: 'أسئلة شائعة',
      q1: 'ما هي الدول التي يتم تغطيتها؟',
      a1: 'نغطي الأسواق الرئيسية في المنطقة بما في ذلك السعودية (اعتماد)، الإمارات، قطر، ونتوسع تدريجياً.',
      q2: 'هل هو مناسب للشركات الصغيرة؟',
      a2: 'نعم. صممنا تنبيهاتنا لمساعدة الشركات الصغيرة على التصرف بسرعة الشركات الكبرى وبدون تكاليف باهظة.',
    },
    auth: {
      login: {
        title: 'مرحباً بعودتك',
        subtitle: 'سجل الدخول لمتابعة مناقصاتك.',
        emailLabel: 'البريد الإلكتروني للعمل',
        passwordLabel: 'كلمة المرور',
        rememberMe: 'تذكرني',
        forgotPassword: 'نسيت كلمة المرور؟',
        submit: 'تسجيل الدخول',
        noAccount: 'ليس لديك حساب؟',
        signUpLink: 'أنشئ حساباً جديداً',
      },
      signup: {
        title: 'ابدأ مجاناً اليوم',
        subtitle: 'انضم للشركات التي تفوز بالمناقصات في المنطقة.',
        workEmail: 'البريد الإلكتروني للعمل',
        password: 'كلمة المرور',
        confirmPassword: 'تأكيد كلمة المرور',
        submit: 'إنشاء الحساب',
        hasAccount: 'لديك حساب بالفعل؟',
        loginLink: 'سجل الدخول بدلاً من ذلك',
        terms: 'بالتسجيل، فإنك توافق على الشروط وسياسة الخصوصية.',
      },
      forgot: {
        title: 'استعادة كلمة المرور',
        subtitle: 'أدخل بريدك وسنرسل لك رابط الاستعادة.',
        submit: 'إرسال رابط الاستعادة',
        back: 'العودة لتسجيل الدخول',
        success: 'تفقد بريدك الإلكتروني للحصول على التعليمات.',
      },
      reset: {
        title: 'تعيين كلمة مرور جديدة',
        subtitle: 'اختر كلمة مرور قوية لحسابك.',
        submit: 'تحديث كلمة المرور',
        success: 'تم تحديث كلمة المرور بنجاح.',
      },
      brand: {
        title: 'منصة ذكاء العطاءات الأكثر ثقة في المنطقة.',
        benefit1: 'تنبيهات فورية من أكثر من ٥٠ مصدراً رسمياً.',
        benefit2: 'ذكاء ثنائي اللغة (عربي وإنجليزي).',
        benefit3: 'مصمم خصيصاً لسرعة وكفاءة الشركات الصغيرة.',
      }
    },
    app: {
      nav: {
        dashboard: 'لوحة التحكم',
        tenders: 'المناقصات',
        matches: 'المطابقات',
        alerts: 'التنبيهات',
        sources: 'المصادر',
        activity: 'النشاط',
        settings: 'الإعدادات',
        account: 'الحساب',
        logout: 'تسجيل الخروج',
      },
      session: {
        verifying: 'جاري التحقق من الجلسة...',
        signedInAs: 'تم تسجيل الدخول باسم',
      },
      topbar: {
        search: 'ابحث عن المناقصات، المصادر، أو المطابقات...',
        notifications: 'التنبيهات',
      },
      preview: {
        stats: {
          active: 'المناقصات النشطة',
          matched: 'مطابقات جديدة',
          sources: 'المصادر المراقبة',
        },
        activityTitle: 'النشاط المباشر',
        status: {
          sourceChecked: 'تم فحص المصدر',
          tenderDetected: 'تم اكتشاف مناقصة جديدة',
          matchCreated: 'تم إنشاء تطابق',
          alertSent: 'تم إرسال تنبيه فوري',
          briefDelivered: 'تم تسليم الملخص اليومي',
        }
      }
    },
    dashboard: {
      hero: {
        greeting: 'صباح الخير، سارة',
        summary: 'وجدنا {n} مناقصات جديدة تطابق ملفك الشخصي اليوم.',
        actions: {
          browse: 'تصفح المناقصات',
          profile: 'تعديل الملف'
        }
      },
      stats: {
        newMatches: 'مطابقات جديدة',
        closingSoon: 'تنتهي قريباً',
        alertsSent: 'تنبيهات مرسلة',
        sources: 'مصادر نشطة'
      },
      priority: {
        title: 'مناقصات ذات أولوية',
        viewAll: 'عرض الكل',
        matchScore: 'تطابق {n}٪',
        daysLeft: 'بقي {n} أيام',
        newLabel: 'جديد'
      },
      activity: {
        title: 'النشاط المباشر',
        filterAll: 'الكل',
        filterSources: 'المصادر',
        filterMatches: 'المطابقات',
        status: {
          check: 'تم فحص المصدر: {name}',
          detect: 'اكتشاف مناقصة في {name}',
          match: 'تم إنشاء تطابق لـ {keyword}',
          alert: 'تم إرسال تنبيه عبر واتساب',
          brief: 'تم تسليم الملخص اليومي'
        }
      },
      sourceHealth: {
        title: 'مراقبة المصادر',
        active: 'نشط',
        delayed: 'متأخر',
        lastCheck: 'آخر فحص: منذ {time}'
      }
    },
    tenders: {
      title: 'اكتشاف المناقصات',
      subtitle: 'تصفح وفلتر الفرص عالية القيمة في الشرق الأوسط.',
      searchPlaceholder: 'ابحث عن العنوان، الجهة، أو المرجع...',
      resultsCount: 'تم العثور على {n} مناقصة',
      filters: {
        title: 'الفلاتر',
        source: 'المصدر',
        status: 'الحالة',
        closing: 'موعد الإغلاق',
        category: 'الفئة',
        matchOnly: 'المطابقة فقط',
        newOnly: 'الجديدة فقط',
        reset: 'إعادة ضبط'
      },
      sort: {
        relevance: 'الأكثر صلة',
        newest: 'الأحدث',
        closingSoon: 'تنتهي قريباً'
      },
      card: {
        viewDetails: 'عرض التفاصيل',
        matchReason: 'تطابق لـ:',
        daysLeft: 'بقي {n} أيام',
        closed: 'مغلقة'
      },
      empty: {
        title: 'لم يتم العثور على مناقصات',
        description: 'حاول تعديل الفلاتر أو كلمات البحث.',
        resetAction: 'مسح الكل'
      }
    },
    details: {
      back: 'العودة للمناقصات',
      actions: {
        official: 'عرض المناقصة الرسمية',
        save: 'حفظ لوقت لاحق',
        share: 'مشاركة',
      },
      labels: {
        entity: 'الجهة المصدرة',
        source: 'المصدر الرسمي',
        closingDate: 'تاريخ الإغلاق',
        openingDate: 'تاريخ الفتح',
        publishedDate: 'تاريخ النشر',
        reference: 'مرجع المناقصة',
        category: 'الفئة',
        urgency: 'الأهمية',
        notAvailable: 'غير متوفر',
      },
      match: {
        title: 'لماذا تم الاختيار؟',
        reason: 'تطابق هذه المناقصة اهتماماتك في {keywords}.',
        confidence: '٩٨٪ درجة المطابقة مع ملفك الشخصي.',
        noKeywords: 'لم يتم تسجيل أي كلمات مطابقة لهذه المناقصة بعد.',
      },
      notifications: {
        title: 'حالة التسليم',
        whatsapp: 'تنبيه واتساب فوري',
        email: 'ملخص البريد الإلكتروني',
        sent: 'تم الإرسال',
        notSent: 'مجدول',
        time: 'تم التسليم في {time}',
        matchedAt: 'تم التطابق في {time}',
        pending: 'لم يتم إرسال أي إشعارات بعد.',
      },
      timeline: {
        title: 'سجل الأحداث',
        sourceChecked: 'تمت مراقبة بوابة المصدر',
        detected: 'تم اكتشاف المناقصة ومعالجتها',
        matched: 'تم تأكيد التطابق مع الملف',
        alerted: 'تم إرسال التنبيه للفريق',
        briefed: 'تم تسليم الملخص اليومي',
        noEvents: 'لا يتوفر سجل نشاط بعد.',
      },
      summaryUnavailable: 'لا يتوفر ملخص بالذكاء الاصطناعي بعد.',
      sourceLink: 'فتح رابط المصدر',
    },
    notifications: {
      title: 'التنبيهات',
      subtitle: 'أدر كيفية ووقت استلام معلومات المناقصات.',
      summary: 'مراقبة أكثر من ٥٠ مصدراً مع تفعيل التنبيهات الفورية.',
      tabs: {
        center: 'مركز التنبيهات',
        preferences: 'التفضيلات',
        history: 'سجل التسليم'
      },
      preferences: {
        channels: 'القنوات',
        types: 'أنواع التسليم',
        language: 'لغة التنبيهات',
        email: 'تنبيهات البريد الإلكتروني',
        whatsapp: 'تنبيهات واتساب',
        whatsappDesc: 'تنبيهات فورية تصل إلى هاتفك مباشرة.',
        instant: 'التنبيهات الفورية',
        instantDesc: 'تُرسل لحظة مطابقة المناقصة لملفك الشخصي.',
        daily: 'الملخص اليومي',
        dailyDesc: 'ملخص صباحي لجميع الفرص الجديدة.',
        langAuto: 'تلقائي (لغة النظام)',
        save: 'حفظ التغييرات'
      },
      history: {
        type: 'النوع',
        status: 'الحالة',
        time: 'الوقت',
        matches: 'المطابقات',
        sent: 'تم التسليم',
        failed: 'فشل',
        pending: 'قيد الانتظار'
      }
    },
    offers: {
      title: 'معلومات دقيقة لكل مرحلة.',
      subtitle: 'اختر مستوى المنصة الذي يتناسب مع حجم عملياتك.',
      plans: [
        { name: 'مستقل', price: 'مجاني', features: ['٣ تنبيهات يومية', 'تنبيهات البريد الإلكتروني', 'ملف كلمات مفتاحية واحد'] },
        { name: 'الشركات الصغيرة والمتوسطة المتميزة', price: '$٤٩/شهرياً', features: ['تنبيهات غير محدودة', 'تكامل واتساب', '٣ ملفات كلمات مفتاحية', 'تحليلات السوق'] },
        { name: 'المؤسسات الكبرى', price: 'حسب الطلب', features: ['بث فوري للمعلومات', 'دخول API', 'مدير حساب مخصص', 'مراجعة الامتثال القانوني'] }
      ]
    },
    smeEnterprise: {
      sme: {
        title: 'مصمم للشركات الصغيرة والمتوسطة',
        desc: 'تكافؤ الفرص. احصل على نفس المعلومات التي تحصل عليها الشركات العالمية بكسر من التكلفة.'
      },
      enterprise: {
        title: 'جاهز للمؤسسات الكبرى',
        desc: 'مراقبة أحجام كبيرة من البيانات مع تكامل قوي لـ API وبروتوكولات أمان مخصصة.'
      }
    },
    trust: {
      title: 'موثوق من قبل الشركات في جميع أنحاء المنطقة.',
      subtitle: 'من الشركات الناشئة المحلية إلى الاستشاريين متعددي الجنسيات.'
    },
    finalCta: {
      title: 'جاهز لتأمين عقدك الرئيسي القادم؟',
      desc: 'انضم إلى أكثر من ٢٠٠٠ شركة لا تفوت أي فرصة.',
      button: 'أنشئ حساباً مجانياً'
    },
    footer: {
      copyright: '© ٢٠٢٦ تندر ووتش. جميع الحقوق محفوظة.',
      links: ['الخصوصية', 'الشروط', 'اتصل بنا']
    }
  }
};
