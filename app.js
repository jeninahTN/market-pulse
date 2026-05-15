// Market Pulse - Main Application Logic

// Service Worker Registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js?v=20260326r4')
            .then(registration => {
                console.log('ServiceWorker registration successful');
                registration.update().catch(() => {});
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Voice Assistant Logic
function speak(text, lang = 'en-US') {
    if ('speechSynthesis' in window) {
        const voices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
        const normalizedLang = String(lang || 'en-US').toLowerCase();
        const baseLang = normalizedLang.split('-')[0];

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 0.95;

        const exactVoice = voices.find((voice) => String(voice.lang || '').toLowerCase() === normalizedLang);
        const baseVoice = voices.find((voice) => String(voice.lang || '').toLowerCase().startsWith(baseLang));
        if (exactVoice || baseVoice) {
            utterance.voice = exactVoice || baseVoice;
        }

        window.speechSynthesis.speak(utterance);
    } else {
        alert("Sorry, your browser doesn't support text-to-speech.");
    }
}

// --- Internationalization (i18n) ---

const translations = {
    'en': {
        // Nav & Footer
        'nav_home': 'Home',
        'nav_ussd': 'USSD Service',
        'nav_offline': 'Offline App',
        'nav_help': 'Help',
        'nav_login': 'Login',
        'footer_rights': '© 2026 Market Pulse Uganda. All rights reserved.',
        'footer_terms': 'Terms',
        'footer_privacy': 'Privacy',
        'footer_contact': 'Contact',

        // Dashboard (Index)
        'welcome_msg': 'Welcome back, Jeninah!',
        'latest_predictions': 'Here are your latest price predictions',
        'btn_new_prediction': 'Get New Price Prediction',
        'header_monitored_crops': 'My Monitored Crops',
        'header_recent_activity': 'Recent Activity',
        'link_view_all': 'View All History',
        'label_predicted_price': 'Predicted Price',
        'menu_my_crops': 'My Crops',
        'menu_locations': 'My Locations',
        'menu_history': 'Prediction History',
        'menu_settings': 'Settings',

        // Detail Page
        'btn_back': 'Back',
        'last_updated': 'Last updated: Today, 8:00 AM',
        'chart_title': 'Price Trend',
        'why_price_high': 'Why the price is high',
        'why_price_low': 'Why the price is low',
        'future_outlook': 'Future Outlook',
        'change_language': 'Change Language:',

        // Offline Page
        'offline_hero_title': 'Your Market Prices, Even Without Internet.',
        'offline_hero_desc': 'Add Market Pulse to your phone\'s home screen for faster, offline access.',
        'btn_add_home': 'Add to My Home Screen',
        'why_add_title': 'Why Add to Home Screen?',
        'feat_offline_title': 'Offline Access',
        'feat_offline_desc': 'See your last saved price predictions when you have no signal.',
        'feat_fast_title': 'Fast & Light',
        'feat_fast_desc': 'The app opens instantly and uses very little data.',
        'feat_easy_title': 'Easy Access',
        'feat_easy_desc': 'Open Market Pulse with one tap from your home screen.',
        'guide_title': 'Simple 3-Step Guide',
        'step_1_title': '1. Open Menu',
        'step_1_desc': 'Tap the menu button (three dots) in your browser.',
        'step_2_title': '2. Select Add',
        'step_2_desc': 'Find and tap on \'Add to Home Screen\' or \'Install app\'.',
        'step_3_title': '3. Confirm',
        'step_3_desc': 'Follow the prompt and find the app icon on your screen.',

        // Help Page
        'help_title': 'Help & Support',
        'help_subtitle': 'We are here to help. Assistance is available in your local language.',
        'help_get_help': 'Get Help Now',
        'call_desc': 'Call for immediate help',
        'btn_call_now': 'Call Now',
        'sms_desc': 'Send us an SMS',
        'btn_sms_now': 'SMS Now',
        'email_desc': 'Email us your query',
        'btn_email_us': 'Email Us',
        'msg_title': 'Send us a Message',
        'label_name': 'Name',
        'ph_name': 'Enter your full name',
        'label_contact': 'Phone Number or Email',
        'ph_contact': 'Your phone or email',
        'label_message': 'Your Message',
        'ph_message': 'How can we help you today?',
        'btn_send_msg': 'Send Message',
        'faq_title': 'Frequently Asked Questions',
        'faq_1': 'How do I check the price of maize?',
        'faq_2': 'What do the colors in the price trend mean?',
        'faq_3': 'How do I change my market location?',
        'faq_4': 'I forgot my password. What do I do?',

        // USSD Page
        'ussd_hero_title': 'Crop Prices are Now a Call Away',
        'ussd_hero_desc': 'No internet? No smartphone? No problem. Get the latest market prices by dialing a simple code on any phone.',
        'btn_how_it_works': 'See How It Works',
        'ussd_steps_title': 'Get Prices in 3 Easy Steps',
        'ussd_steps_desc': 'Follow these simple steps to get price information right on your phone screen.',
        'ussd_step_1_title': 'Dial The Code',
        'ussd_step_1_desc': 'Open your phone\'s dialer and enter this code: *123#. Then press the call button.',
        'ussd_step_2_title': 'Choose Your Crop & Market',
        'ussd_step_2_desc': 'A menu will appear on your screen. Enter the number for your crop (e.g., 1 for Maize), then enter the number for your market (e.g., 2 for Kampala).',
        'ussd_step_3_title': 'Get Price Advice',
        'ussd_step_3_desc': 'You will instantly see the price advice on your screen in your chosen language.',
        'ussd_benefits_title': 'Benefits for Every Farmer',
        'ben_internet_title': 'Works Without Internet',
        'ben_internet_desc': 'Get important market information even if you don\'t have internet data or a smartphone.',
        'ben_instant_title': 'Get Instant Replies',
        'ben_instant_desc': 'Receive price information in seconds, so you can decide quickly when to sell.',
        'ben_profit_title': 'Make More Profit',
        'ben_profit_desc': 'Knowing the right price helps you sell at the best time to earn more from your harvest.',
        'ussd_on_screen': 'On Your Screen:',
        'ussd_reply_1': 'You reply: 1',
        'ussd_final_advice': 'Final Advice:',
        'ussd_demo_msg_1': 'Price rising—sell soon!',
        'ussd_demo_msg_2': 'Bei erinnya - tunda mangu!',

        // Login Page
        'login_subtitle': 'Price insights for your farm.',
        'tab_signin': 'Sign In',
        'tab_signup': 'Create Account',
        'label_login_id': 'Email or Phone Number',
        'ph_login_id': 'e.g. jane@example.com or 07...',
        'label_password': 'Password',
        'ph_password': 'Enter your password',
        'link_forgot': 'Forgot Password?',
        'btn_signin': 'Sign In',
        'btn_google': 'Sign in with Google'
    ,
        'btn_play_advisory': 'Play Voice Advisory'
    },
    'lg': {
        'nav_home': 'Awaka',
        'nav_ussd': 'Obuweereza bwa USSD',
        'nav_offline': 'Enkola ezitali ku mutimbagano',
        'nav_help': 'Yamba',
        'nav_login': 'Okuyingira',
        'footer_rights': '© 2026 Market Pulse Uganda. Obuyinza bwonna bukuumibwa.',
        'footer_terms': 'Ebiragiro',
        'footer_privacy': 'Eby\'ekyama',
        'footer_contact': 'Okukwatagana',
        'welcome_msg': 'Mwaniriziddwa, Jeninah!',
        'latest_predictions': 'Bino by\'osembyeyo okuteebereza ku miwendo',
        'btn_new_prediction': 'Funa Okuteebereza kw\'emiwendo okupya',
        'header_monitored_crops': 'Ebirime byange ebirondoolebwa',
        'header_recent_activity': 'Ebyakolebwa Gyebuvuddeko',
        'link_view_all': 'Laba ebyafaayo byonna',
        'label_predicted_price': 'Emiwendo Egiteeberezebwa',
        'menu_my_crops': 'Ebirime byange',
        'menu_locations': 'Ebifo byange',
        'menu_history': 'Ebyafaayo by\'okuteebereza',
        'menu_settings': 'Entegeka',
        'btn_back': 'Okudda',
        'last_updated': 'Ekisembayo okutereezebwa: Leero, ssaawa 8:00 ez\'oku makya',
        'chart_title': 'Enkula y\'ebbeeyi',
        'why_price_high': 'Lwaki ebbeeyi eri waggulu?',
        'why_price_low': 'Lwaki omuwendo mutono?',
        'future_outlook': 'Ebiseera by\'omumaaso',
        'change_language': 'Kyusa Olulimi:',
        'offline_hero_title': 'Emiwendo gyo egy\'akatale, ne nga tolina yintaneeti.',
        'offline_hero_desc': 'Gattako Market Pulse ku lutimbe lw\'essimu yo olusooka okufuna amangu, nga toli ku mutimbagano.',
        'btn_add_home': 'Gattako ku lutimbe lwange olwasooka',
        'why_add_title': 'Lwaki Oyongerayo ku Home screen?',
        'feat_offline_title': 'Okutuuka ku mutimbagano',
        'feat_offline_desc': 'Laba okulagula kw\'emiwendo gyo ogasembyeyo okutereka nga tolina kabonero.',
        'feat_fast_title': 'Fast & Light',
        'feat_fast_desc': 'App eggulwawo mangu era ekozesa data ntono nnyo.',
        'feat_easy_title': 'Okufuna Amangu',
        'feat_easy_desc': 'Ggulawo Pulse y\'akatale n\'okukwata kumu okuva ku lutimbe lwo olusooka.',
        'guide_title': 'Ekitabo ekirimu emitendera esatu',
        'step_1_title': '1. Ggulawo Menyu',
        'step_1_desc': 'Ttika ku kanyiga ka menu (obutundutundu busatu) mu kunoonya kwo.',
        'step_2_title': '2. Londa Gattako',
        'step_2_desc': 'Funa era onyige ku \'Okwongerako ku Home screen\' oba \'Teekamu app\'\'.',
        'step_3_title': '3. Kakasa',
        'step_3_desc': 'Goberera ekiragiro ofune akabonero ka app ku sikulini yo.',
        'help_title': 'Yamba & Wamba',
        'help_subtitle': 'Tuli wano okuyamba. Obuyambi buliwo mu lulimi lwo.',
        'help_get_help': 'Funa Obuyambi Kati',
        'call_desc': 'Kuba obuyambi obw\'amangu',
        'btn_call_now': 'Kuba Kati',
        'sms_desc': 'Tuweereze obubaka ku ssimu',
        'btn_sms_now': 'Sms Kati',
        'email_desc': 'Tuweereze obubaka bwo ku email',
        'btn_email_us': 'Tuweereze email',
        'msg_title': 'Tuweereze obubaka',
        'label_name': 'Erinnya',
        'ph_name': 'Yingiza erinnya lyo lyonna',
        'label_contact': 'Ennamba y\'essimu oba email',
        'ph_contact': 'Esimu yo oba email yo',
        'label_message': 'Obubaka Bwo',
        'ph_message': 'Tuyinza kukuyamba tutya leero?',
        'btn_send_msg': 'Sindika obubaka',
        'faq_title': 'Ebibuuzo Ebitera Okubuuzibwa',
        'faq_1': 'Nkebera ntya bbeeyi y\'emmwaanyi?',
        'faq_2': 'Langi eziri mu mutindo gw\'ebbeeyi zitegeeza ki?',
        'faq_3': 'Nkyusa ntya ekifo akatale kange we kali?',
        'faq_4': 'Nneerabidde akasumuluzo kange. Nkole ntya?',
        'ussd_hero_title': 'Ebbeeyi y\'ebirime kati eri wala',
        'ussd_hero_desc': 'Tewali mutimbagano? Tewali ssimu? Tewali buzibu. Funa emiwendo gy\'ebyamaguzi egisembyeyo ng\'oyita koodi ennyangu ku ssimu yonna.',
        'btn_how_it_works': 'Laba Engeri Gye Kikolamu',
        'ussd_steps_title': 'Funa emiwendo mu mitendera 3 egyangu',
        'ussd_steps_desc': 'Goberera emitendera gino egyangu okufuna obubaka ku miwendo ku ssimu yo.',
        'ussd_step_1_title': 'Kuba Koodi',
        'ussd_step_1_desc': 'Ggulawo endagiriro y\'essimu yo oyingize koodi eno: *123#. Olwo nyiga ku kakonge k\'okukuba essimu.',
        'ussd_step_2_title': 'Londa Ebirime byo & akatale',
        'ussd_step_2_desc': 'Menyu ejja kulabika ku lutimbe lwo. Yingiza ennamba y\'ekirime kyo (okugeza, 1 ku Kasooli), olwo yingiza ennamba y\'akatale ko (okugeza, 2 ku Kampala).',
        'ussd_step_3_title': 'Funa Amagezi ku miwendo',
        'ussd_step_3_desc': 'Mangu ddala ojja kulaba amagezi ku miwendo ku lutimbe lwo mu lulimi lw\'olonze.',
        'ussd_benefits_title': 'Emigaso eri buli mulimi',
        'ben_internet_title': 'Kikola nga tolina mutimbagano',
        'ben_internet_desc': 'Funa amawulire amakulu agakwata ku katale ne bw\'oba tolina yintaneeti oba essimu.',
        'ben_instant_title': 'Funa ebyokuddamu eby\'amangu',
        'ben_instant_desc': 'Funa obubaka ku bbeeyi mu sikonda, osobole okusalawo amangu ddi lw\'otunda.',
        'ben_profit_title': 'Kola Amagoba Amangi',
        'ben_profit_desc': 'Okumanya omuwendo omutuufu kikuyamba okutunda mu budde obutuufu okufuna ebisingawo okuva mu makungula go.',
        'ussd_on_screen': 'Ku Simu Yo:',
        'ussd_reply_1': 'Oddamu: 1',
        'ussd_final_advice': 'Okuhabula Okusembayo:',
        'ussd_demo_msg_1': 'Ebbeeyi erinnya—tunda mangu!',
        'ussd_demo_msg_2': 'Bei erinnya - tunda mangu!',
        'login_subtitle': 'Amagezi ku bbeeyi ya faamu yo.',
        'tab_signin': 'Wewandiise',
        'tab_signup': 'Tonda akawunti',
        'label_login_id': 'Email oba ennamba y\'essimu',
        'ph_login_id': 'okugeza jane@example.com oba 07...',
        'label_password': 'Akasumulizo',
        'ph_password': 'Yingiza akasumulizo ko',
        'link_forgot': 'Werabidde akasumuluzo?',
        'btn_signin': 'Wewandiise',
        'btn_google': 'Yingira ne Google',
        'btn_play_advisory': 'Zannyisa Amagezi g\'Eddoboozi'
    },
    'rn': {
        'nav_home': 'Omuka',
        'nav_ussd': 'Obuheereza bwa USSD',
        'nav_offline': 'App etari aha mukutu',
        'nav_help': 'Hwera',
        'nav_login': 'Okutaahamu',
        'footer_rights': '© 2026 Market Pulse Uganda. Obugabe bwona buhikire.',
        'footer_terms': 'Ebiragiro',
        'footer_privacy': 'Eby\'okwerinda',
        'footer_contact': 'Okukwatanisa',
        'welcome_msg': 'Wakiira kugaruka, Jeninah!',
        'latest_predictions': 'Ebi nibyo bitengo ebi orikugambireho obwahati',
        'btn_new_prediction': 'Funa okuteebereza kw\'emihendo okusya',
        'header_monitored_crops': 'Ebihingirwe byangye ebirikukyeberwa',
        'header_recent_activity': 'Ebyakozirwe hati',
        'link_view_all': 'Reeba ebyafaayo byona',
        'label_predicted_price': 'Emihendo erikuteekateekwaho',
        'menu_my_crops': 'Ebihingirwe byangye',
        'menu_locations': 'Emyanya yangye',
        'menu_history': 'Ebyafaayo by\'okuteebereza',
        'menu_settings': 'Entebekanisa',
        'btn_back': 'Okugaruka',
        'last_updated': 'Ekyahererukireyo kukorwa: Eriizooba, shaaha 8:00 ez\'akasheeshe',
        'chart_title': 'Enkora y\'emihendo',
        'why_price_high': 'Ahabwenki emihendo eri ahaiguru?',
        'why_price_low': 'Ahabwenki emihendo eri ahansi?',
        'future_outlook': 'Enteekateeka y\'ebiro bya nyensya',
        'change_language': 'Hindura Orurimi:',
        'offline_hero_title': 'Emihendo yaawe y\'akatare, nobu waakuba otaine intaneeti.',
        'offline_hero_desc': 'Oyongyereho Market Pulse aha sikuriini y\'esimu yaawe ey\'okureeberaho kugira ngu otungye ahonaaho, otarikukoresa intaneti.',
        'btn_add_home': 'Yongyera aha terevijoni yangye ey\'omuka',
        'why_add_title': 'Ahabw\'enki orikwongyera aha sikuriini y\'omuka?',
        'feat_offline_title': 'Okuhika aha intaneti etari aha mukutu',
        'feat_offline_desc': 'Reeba ebiteekateeko byawe by\'emihendo eby\'ahamuheru ebirikubiikwa waaba otaine siginiini.',
        'feat_fast_title': 'Kyanguhi & Kyanguhi',
        'feat_fast_desc': 'App neigura ahonaaho kandi nekoresa ebihandiiko bikye munonga.',
        'feat_easy_title': 'Kyanguhi kuhikwaho',
        'feat_easy_desc': 'Guraho akatare pulse n\'okuteera kamwe kuruga aha simu yaawe ey\'omuka.',
        'guide_title': 'Obuhabuzi bw\'emiringo eshatu',
        'step_1_title': '1. Yiguraho menu',
        'step_1_desc': 'Kwata aha kakyebezo k\'eby\'okurya (obubonero bushatu) omu burawuza yaawe.',
        'step_2_title': '2.Ronda Okwongyera',
        'step_2_desc': 'Funa kandi otaahire ahari \'Okwongyera ahakishengye ky\'omuka\' nari \'Teekamu puroguraamu\'.',
        'step_3_title': '3.Hamya',
        'step_3_desc': 'Kuratira ekirikwetagisa osherure akabonero ka puroguraamu aha sikuriini yaawe.',
        'help_title': 'Obuhwezi n\'obuhwezi',
        'help_subtitle': 'Turi aha kuhwera. Obuhwezi buriho omu rurimi rwawe.',
        'help_get_help': 'Funa obuhwezi hati',
        'call_desc': 'Yeta obuhwezi ahonaaho.',
        'btn_call_now': 'Terera Hati',
        'sms_desc': 'Tuheereze obutumwa aha simu',
        'btn_sms_now': 'Ohandikise obutumwa obwahati',
        'email_desc': 'Tuheereze ebaruha aha kubuuza kwawe',
        'btn_email_us': 'Tuheereze email',
        'msg_title': 'Tuheereze obutumwa',
        'label_name': 'Eiziina',
        'ph_name': 'Ta eiziina ryawe ryona',
        'label_contact': 'Enamba y\'esimu nainga email',
        'ph_contact': 'Esimu yaawe nainga email yaawe',
        'label_message': 'Obutumwa bwawe',
        'ph_message': 'Nitubaasa kukuhwera tuta erizooba?',
        'btn_send_msg': 'Sindika obutumwa',
        'faq_title': 'Ebibuuzo ebirikukira kubuzibwa',
        'faq_1': 'Nkakyebera nta omuhendo gw\'ebicoori?',
        'faq_2': 'Erangi eziri omu mibeeyi nizimanyisa ki?',
        'faq_3': 'Nimpindura nta omwanya gw\'akatare kangye?',
        'faq_4': 'Ninyebwa akasumuluzo kangye. Ninkora ki?',
        'ussd_hero_title': 'Emihendo y\'ebihingirwe hati eri haihi',
        'ussd_hero_desc': 'Tihariho intaneeti? Tihariho simu? Tihariho buremeezi. Funa emihendo y\'ebintu eriho obwahati obwo orikuteera koodi aha simu yoona.',
        'btn_how_it_works': 'Reeba oku kirikukora',
        'ussd_steps_title': 'Funa emihendo omu mitendera eshatu',
        'ussd_steps_desc': 'Kuratira engyenderwaho ezi okureeba ebishare aha simu yaawe.',
        'ussd_step_1_title': 'Terera Koodi',
        'ussd_step_1_desc': 'Guraho ekyoma ky\'okuteera esimu yaawe, otaho koodi egi: *123#. Bwanyima gyeza aha kakongi k\'okuteera esimu.',
        'ussd_step_2_title': 'Toorana ebihingirwe byawe n\'akatare',
        'ussd_step_2_desc': 'Meenu neija kureebeka aha sikuriini yaawe. Taho enamba y\'ebihingirwe byawe (nk\'eky\'okureeberaho, 1 eya Maize), reero otaho enamba y\'akatare kaawe (nk\'eky\'ok',
        'ussd_step_3_title': 'Funa obuhabuzi aha bishare',
        'ussd_step_3_desc': 'Obwahati noija kureeba okuhaburwa kw\'emihendo aha sikuriini yaawe omu rurimi oru orikwenda.',
        'ussd_benefits_title': 'Omugasho gwa buri muhingi',
        'ben_internet_title': 'Nikora hatariho intaneeti',
        'ben_internet_desc': 'Funa amakuru ag\'omugasho agarikukwata aha katare nobu waakuba otaine intaneeti nainga esimu.',
        'ben_instant_title': 'Funa eby\'okugarukwamu ahonaaho',
        'ben_instant_desc': 'Funa amakuru g\'emihendo omu sikonda nkye, n\'ahabw\'ekyo noobaasa kusharaho ahonaaho obu orikwenda kuguza.',
        'ben_profit_title': 'Kora Amagoba Maingi',
        'ben_profit_desc': 'Okumanya omuhendo oguhikire nikikuhwera kuguza omu bwire obuhikire, kugira ngu otungye bingi kuruga omu musharuura gwawe.',
        'ussd_on_screen': 'Aha Simu Yawe:',
        'ussd_reply_1': 'Ogaramu: 1',
        'ussd_final_advice': 'Okuhabura Okwahereruka:',
        'ussd_demo_msg_1': 'Omuhendo nigwongyera—guza hati!',
        'ussd_demo_msg_2': 'Bei erinnya - tunda mangu!',
        'login_subtitle': 'Okumanya emihendo ya faamu yaawe.',
        'tab_signin': 'Taho omukono',
        'tab_signup': 'Kora akawunti',
        'label_login_id': 'Email nainga enamba y\'esimu',
        'ph_login_id': 'eky\'okureeberaho, jane@example.com nainga 07...',
        'label_password': 'Akeshereko',
        'ph_password': 'Ta akasumuluzo kaawe',
        'link_forgot': 'Oyebirwe akeshereko?',
        'btn_signin': 'Taho omukono',
        'btn_google': 'Yehandikise na Google',
        'btn_play_advisory': 'Reeba obuhabuzi bw\'eiraka'
    },
    'teo': {
        'nav_home': 'Oreke',
        'nav_ussd': 'Ejanakine loka USSD',
        'nav_offline': 'Aitemonokineta nuka olago',
        'nav_help': 'Ingarakite',
        'nav_login': 'Alomar toma',
        'footer_rights': '© 2026 Market Pulse Uganda. Apedorosio kere idario.',
        'footer_terms': 'Ikisila',
        'footer_privacy': 'Akiro nuka aiyeyea',
        'footer_contact': 'Arucokina',
        'welcome_msg': 'Isukunyunitai bobo, Jeninah',
        'latest_predictions': 'Eraasi nu aomisio kon nuitetiak nuikamunitos itiaisinei',
        'btn_new_prediction': 'Odum Akiro nuitetiak nuikamunitos itiaisinei',
        'header_monitored_crops': 'Apotu eong aanyanarata iraan ka',
        'header_recent_activity': 'Aswamisio nuitetiak',
        'link_view_all': 'Koany akiro kere nukakolo',
        'label_predicted_price': 'Ikapun lu ekotoi',
        'menu_my_crops': 'Iraan ka',
        'menu_locations': 'Aiboisio ka',
        'menu_history': 'Akiro nukakolo nuka aomisio',
        'menu_settings': 'Ainapeta',
        'btn_back': 'Abongun',
        'last_updated': 'Akiro nuitetiak nuitetiak: Lolo, isawan ikanyape lukatupuruc',
        'chart_title': 'Apol naka itiaisinei',
        'why_price_high': 'Kanukinyo epolor etiai?',
        'why_price_low': 'Kanukinyo editor etiai?',
        'future_outlook': 'Aomisio Nuingaren',
        'change_language': 'Ijulakin angajep:',
        'offline_hero_title': 'Ikapun kon luka esokoni, araida emamei elago.',
        'offline_hero_desc': 'Oyangau akiro nuka esokoni toma osirigin luka esimu kon kanu adolokin katipet.',
        'btn_add_home': 'Aiyatakin toma osiriginika luko ore',
        'why_add_title': 'Kanukinyo iyatakina toma osirigin lu ore?',
        'feat_offline_title': 'Adumunun kolago',
        'feat_offline_desc': 'Kosesen aomisio nuka itiaisineikon luitetiak arai emamei ijo esimu.',
        'feat_fast_title': 'Atipet & Atipet',
        'feat_fast_desc': 'Engara app ngin katipet ido itosomaete akiro nu ikidioko.',
        'feat_easy_title': 'Epatana Adumunun',
        'feat_easy_desc': 'Kogeu aiboisit naingadaere ikapun keda atutubet adiope kotelebision kon.',
        'guide_title': 'Aicoreta nuepataka auni',
        'step_1_title': '1. Kogeu emenyu',
        'step_1_desc': 'Kitosom akiro nuka imenyu (iuni) kotoma aingic kon.',
        'step_2_title': '2. Oseu Aiyatakin',
        'step_2_desc': 'Kodum kosodi aipet \'Ayatakin toma airot naka ore\' arai bo \'Ipikakin app\'.',
        'step_3_title': '3. Itigogongor',
        'step_3_desc': 'Otup aicoreta kosodi adumun aanyunet naka app kosirigin kon.',
        'help_title': 'Aingarakin & Agangat',
        'help_subtitle': 'Ijai sio ne kanu aingarakin. Ejai aingarakinio kotoma angajep kon.',
        'help_get_help': 'Odum Aingarakinio Kwana',
        'call_desc': 'Inomak aingarakinio katipet',
        'btn_call_now': 'Inomak kwana esimu',
        'sms_desc': 'Ijuka sio akiro nuka SMS',
        'btn_sms_now': 'Ijukak Akiro Kwape Kwana',
        'email_desc': 'Ijukak sio email aingiset kon',
        'btn_email_us': 'Ijukak sio email',
        'msg_title': 'Ijuka sio akiro',
        'label_name': 'Ekiror',
        'ph_name': 'Ibusakinit jo aipikakin ekonikiror kere',
        'label_contact': 'Enaba lo esimu arai bo email',
        'ph_contact': 'Esimu kon arai bo email kon',
        'label_message': 'Akirokon',
        'ph_message': 'Epone bo ani ipedoria sio aingarakin jo ilolo?',
        'btn_send_msg': 'Ijuka Akiro',
        'faq_title': 'Aingiseta nu etapit aingitingit',
        'faq_1': 'Eipone ali awanyunia eong etiai lo ekirididi?',
        'faq_2': 'Inyoin bo apolou naka iriagin luka etiai?',
        'faq_3': 'Epone bo ani apedoria eong aijulakin aiboisit naka esokoni ka?',
        'faq_4': 'Abu eong imurok akekiro nuka aisubus. Inyoin bo ebeit eong aswam?',
        'ussd_hero_title': 'Apolor kwana itiaisinei luka iraan',
        'ussd_hero_desc': 'Emamei elago? Emamei esimu lo esimu? Emamei ationis. Odum itiaisinei lu iswamaete kosokoni kowai lo ainom kolago.',
        'btn_how_it_works': 'Kosesen Epone Loiswamai',
        'ussd_steps_title': 'Odum itiaisinei koipone kalo epatana',
        'ussd_steps_desc': 'Otup ainapeta nu kanu adumun akiro nuka itiaisinei kosimu kon.',
        'ussd_step_1_title': 'Inom Ekod',
        'ussd_step_1_desc': 'Kogolok aiboisit naka aiwadika esimu kon kosodi aipikakin ekod lo: *123#. Kangin kosodi aipet akinyet naka ainom esimu.',
        'ussd_step_2_title': 'Oseu iraan kon keda esokoni',
        'ussd_step_2_desc': 'Ebuni emenyu abunere kosirigin kon. Ibusakinit jo aipikakin enaaba loka iraan kon (okuju, 1 kanuka Maize), kosodi aipikakin enaaba loka esokoni kon (okuju, 2 kanuka Kampala).',
        'ussd_step_3_title': 'Odum aicoreta nuka itiaisinei',
        'ussd_step_3_desc': 'Ibuni jo asesen aicoreta nuka itiaisinei kotoma angajep na ikoto ijo.',
        'ussd_benefits_title': 'Ajokis naka akoriok kere',
        'ben_internet_title': 'Iswamai komamei elago',
        'ben_internet_desc': 'Odum akiro nuepolok nuikamunitos esokoni araida emameotor ijo keda elago arai isimun.',
        'ben_instant_title': 'Odum abongokineta katipet',
        'ben_instant_desc': 'Odum akiro nuka itiaisinei kotoma atikatikan, tetere ijo ipedori aseun apak na agwelar.',
        'ben_profit_title': 'Iswama Ameda Naepol',
        'ben_profit_desc': 'Ajenun etiai loajokan ingarakini jo agwelar kotoma apak najokan kanu adumun ikapun luipu kotoma aisak.',
        'ussd_on_screen': 'Ko Simu Kon:',
        'ussd_reply_1': 'Iboyene: 1',
        'ussd_final_advice': 'Aicorakinit Naasuban:',
        'ussd_demo_msg_1': 'Etiai epolore—itogwel katipet!',
        'ussd_demo_msg_2': 'Bei erinnya - tunda mangu!',
        'login_subtitle': 'Akiro nuikamunitos itiaisinei luka amisirikon.',
        'tab_signin': 'Iwadikaun',
        'tab_signup': 'Ibusakinit jo aiswamaun akaunta',
        'label_login_id': 'Email arai bo enaaba lo esimu',
        'ph_login_id': 'aanyunet: jane@example.com arai 07...',
        'label_password': 'Akirot na aingada ikapun',
        'ph_password': 'Ibusakinit jo aipikakin akirokon',
        'link_forgot': 'Imurokini kereka jo akirot naka aisubus?',
        'btn_signin': 'Iwadikaun',
        'btn_google': 'Iwadikaun keda Google',
        'btn_play_advisory': 'Kobolia aicoreta nuka iporoto'
    },
    'luo': {
        'nav_home': 'Gang',
        'nav_ussd': 'Tic me USSD',
        'nav_offline': 'Purugram me wiyamo',
        'nav_help': 'Kony',
        'nav_login': 'Donyo',
        'footer_rights': '© 2026 Market Pulse Uganda. Twero weng ogwokke.',
        'footer_terms': 'Cik',
        'footer_privacy': 'Lok me mung',
        'footer_contact': 'Kube',
        'welcome_msg': 'Wajoli cen, Jeninah!',
        'latest_predictions': 'Man aye byek me wel ma itye kwede',
        'btn_new_prediction': 'Nong byek me wel manyen',
        'header_monitored_crops': 'Cam ma abedo ka ngiyo ne',
        'header_recent_activity': 'Tic ma otime cokcok-ki',
        'link_view_all': 'Nen gin mukato weng',
        'label_predicted_price': 'Wel ma kigeno',
        'menu_my_crops': 'Cam ma apito',
        'menu_locations': 'Kabedo na',
        'menu_history': 'Gin mukato me byeko',
        'menu_settings': 'Ter',
        'btn_back': 'Odwogo cen',
        'last_updated': 'Lok manyen me agiki: Tin, cawa apar wiye aryo me odiko',
        'chart_title': 'Kit ma wel tye kawot kwede',
        'why_price_high': 'Pingo wel ne tye lamal tutwal',
        'why_price_low': 'Pingo wel ne tye piny',
        'future_outlook': 'Neno me anyim',
        'change_language': 'Lok Leb:',
        'offline_hero_title': 'Wel me cuk megi, kadi bed ni pe itye ki intanet.',
        'offline_hero_desc': 'Med Market Pulse I wang cim mamegi me gang pi nongo yoo me kube oyot.',
        'btn_add_home': 'Med I My Home screen',
        'why_add_title': 'Pingo Medo I Cuma me gang?',
        'feat_offline_title': 'Nongo ki wiyamo',
        'feat_offline_desc': 'Nen byek me wel ma ki gwoko pi tyen me agiki ka pe itye ki alama.',
        'feat_fast_title': 'Rwatte oyot tutwal',
        'feat_fast_desc': 'Yub eni yabo cutcut dok tiyo ki ngec manok tutwal.',
        'feat_easy_title': 'Yot me nongo ne',
        'feat_easy_desc': 'Yabu puls me cuk ki moto acel ki I wang dirica mamegi me gang.',
        'guide_title': 'Lanyut me yoo adek ma yot',
        'step_1_title': '1. Yabo menu',
        'step_1_desc': 'Gony lyere me menu (lwak adek) i layeny mamegi.',
        'step_2_title': '2. Yer med',
        'step_2_desc': 'Nong kadong igud i kom \'Med i Home screen\' onyo \'Ket app\'\'.',
        'step_3_title': '3. Moko',
        'step_3_desc': 'Lub cik me nongo lanyut me purugram i kom dirica mamegi.',
        'help_title': 'Kony & Kony',
        'help_subtitle': 'Watye kany me konyo. Kony tye I leb ma megi.',
        'help_get_help': 'Nong Kony Kombedi',
        'call_desc': 'Go cim pi kony oyot oyot',
        'btn_call_now': 'Go cim kombedi',
        'sms_desc': 'Cwali wa SMS',
        'btn_sms_now': 'Cwal SMS Kombedi',
        'email_desc': 'Cwali wa lapeny mamegi ki email',
        'btn_email_us': 'Cwali wa email',
        'msg_title': 'Cwaliwa kwena',
        'label_name': 'Nying',
        'ph_name': 'Ket nyingi maleng',
        'label_contact': 'Namba me cim onyo email',
        'ph_contact': 'Cimmi onyo email mamegi',
        'label_message': 'Kwena ni',
        'ph_message': 'Watwero konyi nining tin?',
        'btn_send_msg': 'Cwal kwena',
        'faq_title': 'Lapeny ma ki penyo I kare weng',
        'faq_1': 'Atwero ngiyo wel anyogi nining?',
        'faq_2': 'Rangi matye I rwom me wel enoni tyen lokke ngo?',
        'faq_3': 'Aloko nining kama cuk mega tye iye?',
        'faq_4': 'Wiya owil ki mung me donyo. Ngo ma myero atim?',
        'ussd_hero_title': 'Wel cam dong tye kama bor tutwal',
        'ussd_hero_desc': 'Pe tye intanet? Pe tye cim cing makilwongo ni smartphone? Pe tye peko. Nong wel me cuk matye manyen kun i goyo code ma yot I cim mo keken.',
        'btn_how_it_works': 'Nen kit ma tiyo kwede',
        'ussd_steps_title': 'Nong Wel I yoo ma yot 3',
        'ussd_steps_desc': 'Lub yoo matino-tino magi me nongo ngec me wel icim mamegi.',
        'ussd_step_1_title': 'Gony Kod',
        'ussd_step_1_desc': 'Yabo dialer me cimmi kadong i ket code man: *123#. Ci di kit me goyo cim.',
        'ussd_step_2_title': 'Yer cam mamegi ki cuk',
        'ussd_step_2_desc': 'Menu bi nen iwi dirica mamegi. Ket namba me cam mamegi (e.g., 1 pi anyogi), kadong ket namba me cuk mamegi (e.g., 2 pi Kampala).',
        'ussd_step_3_title': 'Nong tam pi wel',
        'ussd_step_3_desc': 'Cutcut I bineno ngec me wel I leb ma imito.',
        'ussd_benefits_title': 'Ber pa lupur weng',
        'ben_internet_title': 'Tic labongo intanet',
        'ben_internet_desc': 'Nong ngec mapire tek I kom cat kadi bed pe itye ki intanet onyo cim cing.',
        'ben_instant_title': 'Nong Lagam ma oyotoyot',
        'ben_instant_desc': 'Nong ngec me wel I nge cekon, wek imok tam oyot ikare me cat.',
        'ben_profit_title': 'Bed ki magoba madwong',
        'ben_profit_desc': 'Ngeyo wel ma opore weko icato i kare ma opore me nongo magoba madwong.',
        'ussd_on_screen': 'I Simu Ni:',
        'ussd_reply_1': 'Idok iye: 1',
        'ussd_final_advice': 'Tamme Me Agikki:',
        'ussd_demo_msg_1': 'Wel tye kawot lamal—cat cut!',
        'ussd_demo_msg_2': 'Bei erinnya - tunda mangu!',
        'login_subtitle': 'Ngec matut I kom wel me poto ni.',
        'tab_signin': 'Ket Cingi',
        'tab_signup': 'Yub account',
        'label_login_id': 'Email onyo Namba me Cim',
        'ph_login_id': 'me lapore jane@example.com onyo 07...',
        'label_password': 'Mung me donyo',
        'ph_password': 'Ket mung me donyo mamegi',
        'link_forgot': 'Wiyi owil ki mung me donyo?',
        'btn_signin': 'Ket Cingi',
        'btn_google': 'Donyo ki Google',
        'btn_play_advisory': 'Tuko Voice Advisory'
    },
    'sw': {
        // Nav & Footer
        'nav_home': 'Nyumbani',
        'nav_ussd': 'Huduma ya USSD',
        'nav_offline': 'Programu ya Nje ya Mtandao',
        'nav_help': 'Msaada',
        'nav_login': 'Ingia',
        'footer_rights': '© 2026 Market Pulse Uganda. Haki zote zimehifadhiwa.',
        'footer_terms': 'Masharti',
        'footer_privacy': 'Faragha',
        'footer_contact': 'Wasiliana',

        // Dashboard (Index)
        'welcome_msg': 'Karibu tena, Jeninah!',
        'latest_predictions': 'Hapa kuna utabiri wako wa hivi karibuni wa bei',
        'btn_new_prediction': 'Pata Utabiri Mpya wa Bei',
        'header_monitored_crops': 'Mazao Yangu Yanayofuatiliwa',
        'header_recent_activity': 'Shughuli za Hivi Karibuni',
        'link_view_all': 'Tazama Historia Yote',
        'label_predicted_price': 'Bei Inayotabiriwa',
        'menu_my_crops': 'Mazao Yangu',
        'menu_locations': 'Maeneo Yangu',
        'menu_history': 'Historia ya Utabiri',
        'menu_settings': 'Mipangilio',

        // Detail Page
        'btn_back': 'Nyuma',
        'last_updated': 'Ilisasishwa: Leo, 8:00 Asubuhi',
        'chart_title': 'Mwelekeo wa Bei',
        'why_price_high': 'Kwa nini bei ni juu',
        'why_price_low': 'Kwa nini bei ni chini',
        'future_outlook': 'Mtazamo wa Baadaye',
        'change_language': 'Badili Lugha:',

        // Offline Page
        'offline_hero_title': 'Bei za Soko Lako, Hata Bila Intaneti.',
        'offline_hero_desc': 'Ongeza Market Pulse kwenye skrini yako ya nyumbani kwa ufikiaji wa haraka bila mtandao.',
        'btn_add_home': 'Ongeza kwenye Skrini Yangu ya Nyumbani',
        'why_add_title': 'Kwa Nini Ongeza kwenye Skrini ya Nyumbani?',
        'feat_offline_title': 'Ufikiaji Bila Mtandao',
        'feat_offline_desc': 'Tazama utabiri wako wa bei uliohifadhiwa wakati huna ishara.',
        'feat_fast_title': 'Haraka na Nyepesi',
        'feat_fast_desc': 'Programu inafunguka mara moja na hutumii data nyingi.',
        'feat_easy_title': 'Ufikiaji Rahisi',
        'feat_easy_desc': 'Fungua Market Pulse kwa bomba moja kutoka skrini yako ya nyumbani.',
        'guide_title': 'Mwongozo Rahisi wa Hatua 3',
        'step_1_title': '1. Fungua Menyu',
        'step_1_desc': 'Gonga kitufe cha menyu (nukta tatu) kwenye kivinjari chako.',
        'step_2_title': '2. Chagua Ongeza',
        'step_2_desc': 'Tafuta na ugonge \'Ongeza kwenye Skrini ya Nyumbani\' au \'Sakinisha programu\'.',
        'step_3_title': '3. Thibitisha',
        'step_3_desc': 'Fuata maagizo na upate ikoni ya programu kwenye skrini yako.',

        // Help Page
        'help_title': 'Msaada na Usaidizi',
        'help_subtitle': 'Tuko hapa kukusaidia. Msaada unapatikana katika lugha yako ya eneo.',
        'help_get_help': 'Pata Msaada Sasa',
        'call_desc': 'Piga simu kwa msaada wa haraka',
        'btn_call_now': 'Piga Simu Sasa',
        'sms_desc': 'Tutumie SMS',
        'btn_sms_now': 'Tuma SMS Sasa',
        'email_desc': 'Tutumie swali lako kwa barua pepe',
        'btn_email_us': 'Tutumie Barua Pepe',
        'msg_title': 'Tutumie Ujumbe',
        'label_name': 'Jina',
        'ph_name': 'Ingiza jina lako kamili',
        'label_contact': 'Namba ya Simu au Barua Pepe',
        'ph_contact': 'Simu yako au barua pepe yako',
        'label_message': 'Ujumbe Wako',
        'ph_message': 'Tunawezaje kukusaidia leo?',
        'btn_send_msg': 'Tuma Ujumbe',
        'faq_title': 'Maswali Yanayoulizwa Mara Kwa Mara',
        'faq_1': 'Ninawezaje kuangalia bei ya mahindi?',
        'faq_2': 'Rangi katika mwelekeo wa bei zinamaanisha nini?',
        'faq_3': 'Ninawezaje kubadilisha eneo langu la soko?',
        'faq_4': 'Nimesahau nenosiri langu. Nifanye nini?',

        // USSD Page
        'ussd_hero_title': 'Bei za Mazao Sasa Ziko Karibu na Simu Yako',
        'ussd_hero_desc': 'Hakuna intaneti? Hakuna simu ya kisasa? Hakuna shida. Pata bei za soko kwa kupiga nambari rahisi kwenye simu yoyote.',
        'btn_how_it_works': 'Tazama Inavyofanya Kazi',
        'ussd_steps_title': 'Pata Bei kwa Hatua 3 Rahisi',
        'ussd_steps_desc': 'Fuata hatua hizi rahisi kupata habari za bei moja kwa moja kwenye simu yako.',
        'ussd_step_1_title': 'Piga Nambari',
        'ussd_step_1_desc': 'Fungua kipiga-simu chako na uingize nambari hii: *123#. Kisha bonyeza kitufe cha kupiga simu.',
        'ussd_step_2_title': 'Chagua Zao lako na Soko',
        'ussd_step_2_desc': 'Menyu itaonekana kwenye skrini yako. Ingiza nambari ya zao lako (mfano, 1 kwa Mahindi), kisha ingiza nambari ya soko lako (mfano, 2 kwa Kampala).',
        'ussd_step_3_title': 'Pata Ushauri wa Bei',
        'ussd_step_3_desc': 'Utaona mara moja ushauri wa bei kwenye skrini yako katika lugha uliyochagua.',
        'ussd_benefits_title': 'Faida kwa Kila Mkulima',
        'ben_internet_title': 'Inafanya Kazi Bila Intaneti',
        'ben_internet_desc': 'Pata habari muhimu za soko hata kama huna data ya intaneti au simu ya kisasa.',
        'ben_instant_title': 'Pata Majibu ya Haraka',
        'ben_instant_desc': 'Pata taarifa za bei kwa sekunde, ili uweze kuamua haraka lini wa kuuza.',
        'ben_profit_title': 'Pata Faida Zaidi',
        'ben_profit_desc': 'Kujua bei sahihi kukusaidia kuuza wakati sahihi kupata zaidi kutoka kwa mavuno yako.',
        'ussd_on_screen': 'Kwenye Skrini Yako:',
        'ussd_reply_1': 'Unajibu: 1',
        'ussd_final_advice': 'Ushauri wa Mwisho:',
        'ussd_demo_msg_1': 'Bei inapanda—uza hivi karibuni!',
        'ussd_demo_msg_2': 'Bei erinnya - tunda mangu!',

        // Login Page
        'login_subtitle': 'Maarifa ya bei kwa shamba lako.',
        'tab_signin': 'Ingia',
        'tab_signup': 'Unda Akaunti',
        'label_login_id': 'Barua Pepe au Namba ya Simu',
        'ph_login_id': 'mfano: jane@example.com au 07...',
        'label_password': 'Nenosiri',
        'ph_password': 'Ingiza nenosiri lako',
        'link_forgot': 'Umesahau Nenosiri?',
        'btn_signin': 'Ingia',
        'btn_google': 'Ingia na Google',
        'btn_play_advisory': 'Cheza Ushauri wa Sauti'
    }
};

function updateLanguage(lang) {
    if (!translations[lang]) return;

    // Save preference
    localStorage.setItem('preferred_language', lang);

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[lang][key]) {
            // Handle input placeholders specifically
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translations[lang][key];
            } else {
                element.innerText = translations[lang][key];
            }
        }
    });

    // Update dropdown value if it exists
    const selector = document.getElementById('language-selector');
    if (selector) {
        selector.value = lang;
    }
}

// Initialize Language
document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('preferred_language') || 'en';
    updateLanguage(savedLang);

    // --- Mobile Nav Toggle ---
    const navToggle = document.getElementById('nav-toggle');
    const navPanel = document.getElementById('nav-panel');

    if (navToggle && navPanel) {
        const icon = navToggle.querySelector('i');

        const setNavOpen = (open) => {
            navPanel.classList.toggle('open', open);
            navToggle.setAttribute('aria-expanded', String(open));
            if (icon) {
                icon.className = open ? 'fas fa-times' : 'fas fa-bars';
            }
        };

        const closeNav = () => setNavOpen(false);

        navToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const isOpen = navPanel.classList.contains('open');
            setNavOpen(!isOpen);
        });

        navPanel.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    closeNav();
                }
            });
        });

        document.addEventListener('click', (event) => {
            if (window.innerWidth > 768) {
                return;
            }
            if (!navPanel.contains(event.target) && !navToggle.contains(event.target)) {
                closeNav();
            }
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                closeNav();
            }
        });
    }

    // --- Theme Toggle Logic ---
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        
        // Update icon on load
        const currentTheme = document.documentElement.getAttribute('data-theme');
        icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';

        themeToggle.addEventListener('click', () => {
            const theme = document.documentElement.getAttribute('data-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update Icon
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        });
    }

    const selector = document.getElementById('language-selector');
    if (selector) {
        selector.value = savedLang;
        selector.addEventListener('change', (e) => {
            updateLanguage(e.target.value);
        });
    }
});
