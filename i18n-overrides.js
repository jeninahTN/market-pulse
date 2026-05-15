(function () {
    if (typeof translations === 'undefined') {
        return;
    }

    const EN_EXTRA = {
        alert_audio_failed_local: 'Local language audio is temporarily unavailable. Playing a device voice instead.',
        farmer_advice: "Farmer's Advisory",
        recommended_action: 'Recommended Action',
        market_factors: 'Market Factors',
        btn_remove: 'Remove',
        btn_refresh_data: 'Refresh Data',
        insight_decrease_2w: 'Prices may decrease in 2 weeks',
        insight_decrease_2w_desc: 'As the main harvest season begins, more supply is expected, which could lead to lower prices.',
        insight_high_demand: 'High Demand',
        insight_high_demand_desc: 'Increased demand from nearby towns and urban centers is driving prices up.',
        insight_low_supply: 'Low Supply',
        insight_low_supply_desc: 'Fewer farmers are bringing produce to the market this week, reducing available supply.',
        label_select_crop: 'Select Crop',
        label_select_market: 'Select Market / Region',
        link_back_dashboard: 'Back to Dashboard',
        msg_get_started: 'Get started by predicting your first crop price.',
        msg_no_predictions: 'No predictions yet',
        msg_no_predictions_desc: 'You have not monitored any crops or requested price forecasts yet. Click the button above to start your first prediction.',
        opt_choose_crop: 'Choose a crop...',
        opt_choose_market: 'Choose a market...',
        predict_desc: 'Select your crop and local market to see the 1-step price forecast.',
        predict_title: 'Get Price Prediction',
        text_for: 'for',
        text_in: 'in',
        text_welcome: 'Welcome',
        text_welcome_back: 'Welcome back',
        title_current_price: 'Current Price',
        title_predicted_price_source: 'Predicted Price',
        status_online: 'Online',
        status_offline: 'Offline',
        status_online_title: 'Live connection available',
        status_offline_title: 'Offline mode. Cached predictions are available.',
        btn_loading_advisory: 'Loading...',
        btn_playing_advisory: 'Playing...',
        alert_audio_failed: 'Could not load audio advisory.',
        toast_offline_redirect: 'You are offline. Showing the cached or bundled prediction.',
        toast_refresh_requires_connection: 'Refresh needs a connection. Cached predictions are still available.',
        toast_signin_refresh: 'Please sign in again to refresh data.',
        toast_refresh_completed: 'Refresh completed successfully.',
        toast_refresh_failed: 'Refresh failed.',
        toast_connection_restored: 'Connection restored. Market Pulse will refresh cached data.',
        toast_you_are_offline: 'You are offline. Cached and bundled predictions are available.',
        cached_prediction_title: 'Cached Prediction',
        current_label: 'Current',
        forecast_label: 'Forecast',
        advice_label: 'Advice:',
        open_full_detail: 'Open Full Detail',
        no_cached_selection_title: 'No cached prediction for this selection yet',
        no_cached_selection_desc: 'Connect once to refresh the data for this crop and region, then reopen the app while offline.',
        no_saved_predictions: 'No saved predictions are available on this device yet.',
        offline_prediction_ready: 'Offline Prediction Ready',
        offline_intro_synced: 'Market Pulse is showing the last saved prediction that was synced to this browser.',
        offline_intro_bundle: 'This browser computed the forecast locally from the bundled model and the cached weather, sentiment, and price seed data.',
        saved_predictions_device: 'Saved Predictions on This Device'
    };

    const SW_EXTRA = {
        alert_audio_failed_local: 'Sauti ya lugha ya eneo haipatikani kwa sasa. Tunatumia sauti ya kifaa.',
        farmer_advice: 'Ushauri wa Mkulima',
        recommended_action: 'Hatua Iliyopendekezwa',
        market_factors: 'Mambo ya Soko',
        btn_remove: 'Ondoa',
        btn_refresh_data: 'Sasisha Data',
        label_select_crop: 'Chagua Zao',
        label_select_market: 'Chagua Soko / Mkoa',
        link_back_dashboard: 'Rudi kwenye Dashibodi',
        msg_get_started: 'Anza kwa kutabiri bei ya kwanza ya zao lako.',
        msg_no_predictions: 'Bado hakuna utabiri',
        opt_choose_crop: 'Chagua zao...',
        opt_choose_market: 'Chagua soko...',
        predict_desc: 'Chagua zao na soko lako kuona utabiri wa hatua moja wa bei.',
        predict_title: 'Pata Utabiri wa Bei',
        text_for: 'kwa',
        text_in: 'katika',
        text_welcome: 'Karibu',
        text_welcome_back: 'Karibu tena',
        title_current_price: 'Bei ya Sasa',
        title_predicted_price_source: 'Bei Inayotabiriwa',
        status_online: 'Mtandaoni',
        status_offline: 'Nje ya mtandao',
        btn_loading_advisory: 'Inapakia...',
        btn_playing_advisory: 'Inacheza...',
        msg_no_predictions_desc: 'Bado hujafuatilia mazao wala kuomba utabiri wa bei. Bonyeza kitufe hapo juu kuanza utabiri wako wa kwanza.',
        insight_high_demand: 'Mahitaji Makubwa',
        insight_high_demand_desc: 'Mahitaji makubwa kutoka miji ya karibu yanaendelea kupandisha bei.',
        insight_low_supply: 'Upatikanaji Mdogo',
        insight_low_supply_desc: 'Wakulima wachache wameleta mazao sokoni wiki hii, hivyo upatikanaji umepungua.',
        insight_decrease_2w: 'Bei zinaweza kushuka ndani ya wiki 2',
        insight_decrease_2w_desc: 'Msimu mkuu wa mavuno unapoanza, upatikanaji unaweza kuongezeka na kushusha bei.'
    };

    const LG_EXTRA = {
        alert_audio_failed_local: "Eddoboozi ly'olulimi luno teryafunibwa kati. Tukozesa eddoboozi ly'essimu.",
        farmer_advice: "Amagezi g'Omulimi",
        recommended_action: 'Ekyokukola ekiteereddwa',
        market_factors: "Ensonga z'Akatale",
        btn_remove: 'Ggyaawo',
        btn_refresh_data: 'Ddamu okutereeza data',
        label_select_crop: 'Londa ekirime',
        label_select_market: 'Londa akatale / kitundu',
        link_back_dashboard: 'Ddayo ku dashboard',
        msg_get_started: 'Tandika n okuteebereza omuwendo gw ekirime kyo ogusooka.',
        msg_no_predictions: 'Tewali kuteebereza',
        opt_choose_crop: 'Londa ekirime...',
        opt_choose_market: 'Londa akatale...',
        predict_title: 'Funa Okuteebereza kw Emiwendo',
        text_for: 'ku',
        text_in: 'mu',
        text_welcome: 'Mwaniriziddwa',
        text_welcome_back: 'Mwaniriziddwa nate',
        title_current_price: 'Omuwendo gwa kati',
        title_predicted_price_source: 'Omuwendo oguteeberezebwa',
        status_online: 'Ku mutimbagano',
        status_offline: 'Temuli mutimbagano',
        feat_fast_title: 'Kyangu era Kizito Kitono',
        predict_desc: 'Londa ekirime n akatale ko olabe okuteebereza kw omuwendo oguddako.',
        msg_no_predictions_desc: 'Tonnalonda birime bya kulondoola wadde okusaba kuteebereza muwendo. Nyiga ku button waggulu okutandika.',
        insight_high_demand: 'Obwetaavu Bungi',
        insight_high_demand_desc: 'Obwetaavu okuva mu bibuga eby okumpi bulinya emiwendo.',
        insight_low_supply: 'Obungi Butono',
        insight_low_supply_desc: 'Abalimi batono baleese ebirime ku katale wiki eno, ne kikka ku bungi obuliwo.',
        insight_decrease_2w: 'Emiwendo giyinza okukka mu wiiki 2',
        insight_decrease_2w_desc: 'Omusana gw amakungula omukulu bwe gutandika, obungi buyinza okweyongera ne bukendeeza emiwendo.'
    };

    const RN_EXTRA = {
        alert_audio_failed_local: "Eiraka ry'olulimi luno tiririho hati. Nitukozesa eiraka ry'ekyuma.",
        farmer_advice: "Amagezi g'Omurimi",
        recommended_action: "Ekikorwa ekirikwetwa",
        market_factors: "Enshonga z'Akatale",
        btn_remove: 'Gyaho',
        btn_refresh_data: 'Garura Data',
        label_select_crop: 'Toorana ekihingirwe',
        label_select_market: 'Toorana akatare / ekicweka',
        link_back_dashboard: 'Garuka aha dashboard',
        msg_no_predictions: 'Tihariho kuteebereza',
        opt_choose_crop: 'Toorana ekihingirwe...',
        opt_choose_market: 'Toorana akatare...',
        predict_title: 'Funa Okuteebereza kw Emihendo',
        text_for: 'aha',
        text_in: 'omu',
        text_welcome: 'Wakiire',
        text_welcome_back: 'Wakiire garuka',
        title_current_price: 'Omuhendo gwa hati',
        title_predicted_price_source: 'Omuhendo oguteekateekwa',
        status_online: 'Ori aha mutimbagano',
        status_offline: 'Tori aha mutimbagano',
        msg_get_started: 'Tandika n okuteebereza omuhendo gw ekihingirwe kyawe eky okusooka.',
        predict_desc: 'Toorana ekihingirwe n akatare kawe oreebe okuteebereza kw omuhendo oguraakurataho.',
        msg_no_predictions_desc: 'Toratandikire kukyebera bihingirwe byawe nari kusaba kutebereza muhendo. Nyiga aha button ya ruguru otandike.',
        insight_high_demand: 'Obwetaago Bungi',
        insight_high_demand_desc: 'Obwetaago kuruga omu bicweka eby hafi nibuhingisa emihendo.',
        insight_low_supply: 'Obungi Bukye',
        insight_low_supply_desc: 'Abahingi bake bareetsire ebihingirwe aha katare wiki egi, omugabo nigukye.',
        insight_decrease_2w: 'Emihendo neebaasa kugaruka ahansi omu wiki 2',
        insight_decrease_2w_desc: 'Obusiza obukuru bw ebihingirwe nibwatandika, obungi nibubaasa kweyongera emihendo neehika ahansi.'
    };

    const TEO_EXTRA = {
        btn_remove: 'Kwar',
        btn_refresh_data: 'Kitopol data',
        label_select_crop: 'Iseu iraan',
        label_select_market: 'Iseu esokoni / aiboisit',
        link_back_dashboard: 'Abongu dashboard',
        msg_no_predictions: 'Emamei aomisio',
        opt_choose_crop: 'Iseu iraan...',
        opt_choose_market: 'Iseu esokoni...',
        predict_title: 'Odum Aomisio nu Itiaisinei',
        text_for: 'loka',
        text_in: 'aiboisit',
        text_welcome: 'Karibu',
        text_welcome_back: 'Karibu bobo',
        title_current_price: 'Ikapun nu cut',
        title_predicted_price_source: 'Ikapun nu itetiak',
        status_online: 'On line',
        status_offline: 'Off line',
        msg_get_started: 'Kojai akiro nuka aomisio ikapun nu iraan kon naodit.',
        predict_desc: 'Iseu iraan ido esokoni kon kanu ijo anyun aomisio nu ikapun naebuni.',
        msg_no_predictions_desc: 'Inyo emamei iraan ijo ikeyeu nara emamei aomisio nuka ikapun ijo ikisub. Peta button loipeta kogeun.',
        insight_high_demand: 'Atemar Napeol',
        insight_high_demand_desc: 'Atemar nu epol dauni luka aiboisio na ikidioko etubuni ikapun duc.',
        insight_low_supply: 'Aperio na Itunga Ikidioko',
        insight_low_supply_desc: 'Akiro ka idin nuka iyauni iraan toma esokoni ewiki na, iwate aperio ngesi ikidioko.',
        insight_decrease_2w: 'Ikapun epedori adakin kotoma wiki 2',
        insight_decrease_2w_desc: 'Ka epone naka aswamat nu ikarisio egolokino, aperio epedori apeleikina ido ikapun adak.'
    };

    const LUO_EXTRA = {
        btn_remove: 'Kwany',
        btn_refresh_data: 'Yub Data manyen',
        label_select_crop: 'Yer cam',
        label_select_market: 'Yer cuk / kabedo',
        link_back_dashboard: 'Dwok i dashboard',
        msg_no_predictions: 'Byek pe tye',
        opt_choose_crop: 'Yer cam...',
        opt_choose_market: 'Yer cuk...',
        predict_title: 'Nong Byek me Wel',
        text_for: 'pi',
        text_in: 'i',
        text_welcome: 'Wajoli',
        text_welcome_back: 'Wajoli cen',
        title_current_price: 'Wel kombedi',
        title_predicted_price_source: 'Wel ma kigeno',
        status_online: 'Online',
        status_offline: 'Offline',
        msg_get_started: 'Cak ki byeko wel me cam mamegi me acel.',
        predict_desc: 'Yer cam ki cuk mamegi wek ine byeko me wel ma bino.',
        msg_no_predictions_desc: 'In pe ibedo ka ngiyo cam mo onyo penyo byek me wel. Dii buton ma malo wek icak.',
        insight_high_demand: 'Tem marom i wang',
        insight_high_demand_desc: 'Dwong pa tem ki i gang ma cok medde ka cako wel malo.',
        insight_low_supply: 'Cam manok i cuk',
        insight_low_supply_desc: 'Lupur manok aye otedo cam i cuk wiki man, omiyo supply ochung manok.',
        insight_decrease_2w: 'Wel twero bedo piny i wiki 2',
        insight_decrease_2w_desc: 'Ka kare me keyo maduong ocako, supply twero medde ki keto wel piny.'
    };

    const CROP_BY_LANG = {
        en: {
            crop_maize: 'Maize',
            crop_beans: 'Beans',
            crop_cassava: 'Cassava',
            crop_matooke: 'Matooke',
            crop_coffee: 'Coffee'
        },
        lg: {
            crop_maize: 'Kasooli',
            crop_beans: 'Ebijanjaalo',
            crop_cassava: 'Muwogo',
            crop_matooke: 'Matooke',
            crop_coffee: 'Ammwanyi'
        },
        rn: {
            crop_maize: 'Kibindukye',
            crop_beans: 'Ebihimba',
            crop_cassava: 'Muhogo',
            crop_matooke: 'Ebitookye',
            crop_coffee: 'Omwani'
        },
        teo: {
            crop_maize: 'Ekitwala',
            crop_beans: 'Emar',
            crop_cassava: 'Eogo',
            crop_matooke: 'Ebitooke',
            crop_coffee: 'Emwanyi'
        },
        luo: {
            crop_maize: 'Anyanya',
            crop_beans: 'Muranga',
            crop_cassava: 'Gwana',
            crop_matooke: 'Matoke',
            crop_coffee: 'Kawa'
        },
        sw: {
            crop_maize: 'Mahindi',
            crop_beans: 'Maharage',
            crop_cassava: 'Mhogo',
            crop_matooke: 'Ndizi',
            crop_coffee: 'Kahawa'
        }
    };

    const MARKET_BY_LANG = {
        en: {
            market_nakawa: 'Nakawa Market',
            market_owino: 'Owino Market',
            market_kalerwe: 'Kalerwe Market',
            market_masaka: 'Masaka Market',
            market_mbale: 'Mbale Market',
            market_gulu: 'Gulu Market',
            market_kasese: 'Kasese Market',
            market_nankulabye: 'Nankulabye Market',
            market_kamwokya: 'Kamwokya Market'
        },
        lg: {
            market_nakawa: 'Akatale k e Nakawa',
            market_owino: 'Akatale k e Owino',
            market_kalerwe: 'Akatale k e Kalerwe',
            market_masaka: 'Akatale k e Masaka',
            market_mbale: 'Akatale k e Mbale',
            market_gulu: 'Akatale k e Gulu',
            market_kasese: 'Akatale k e Kasese',
            market_nankulabye: 'Akatale k e Nankulabye',
            market_kamwokya: 'Akatale k e Kamwokya'
        },
        rn: {
            market_nakawa: 'Akatare ka Nakawa',
            market_owino: 'Akatare ka Owino',
            market_kalerwe: 'Akatare ka Kalerwe',
            market_masaka: 'Akatare ka Masaka',
            market_mbale: 'Akatare ka Mbale',
            market_gulu: 'Akatare ka Gulu',
            market_kasese: 'Akatare ka Kasese',
            market_nankulabye: 'Akatare ka Nankulabye',
            market_kamwokya: 'Akatare ka Kamwokya'
        },
        teo: {
            market_nakawa: 'Nakawa Market',
            market_owino: 'Owino Market',
            market_kalerwe: 'Kalerwe Market',
            market_masaka: 'Masaka Market',
            market_mbale: 'Mbale Market',
            market_gulu: 'Gulu Market',
            market_kasese: 'Kasese Market',
            market_nankulabye: 'Nankulabye Market',
            market_kamwokya: 'Kamwokya Market'
        },
        luo: {
            market_nakawa: 'Cuk me Nakawa',
            market_owino: 'Cuk me Owino',
            market_kalerwe: 'Cuk me Kalerwe',
            market_masaka: 'Cuk me Masaka',
            market_mbale: 'Cuk me Mbale',
            market_gulu: 'Cuk me Gulu',
            market_kasese: 'Cuk me Kasese',
            market_nankulabye: 'Cuk me Nankulabye',
            market_kamwokya: 'Cuk me Kamwokya'
        },
        sw: {
            market_nakawa: 'Soko la Nakawa',
            market_owino: 'Soko la Owino',
            market_kalerwe: 'Soko la Kalerwe',
            market_masaka: 'Soko la Masaka',
            market_mbale: 'Soko la Mbale',
            market_gulu: 'Soko la Gulu',
            market_kasese: 'Soko la Kasese',
            market_nankulabye: 'Soko la Nankulabye',
            market_kamwokya: 'Soko la Kamwokya'
        }
    };

    function withEnglish(base) {
        return Object.assign({}, EN_EXTRA, base || {});
    }

    const EXTRA_BY_LANG = {
        en: EN_EXTRA,
        lg: withEnglish(LG_EXTRA),
        rn: withEnglish(RN_EXTRA),
        teo: withEnglish(TEO_EXTRA),
        luo: withEnglish(LUO_EXTRA),
        sw: withEnglish(SW_EXTRA)
    };

    Object.keys(EXTRA_BY_LANG).forEach((lang) => {
        if (!translations[lang]) {
            translations[lang] = {};
        }
        Object.assign(translations[lang], EXTRA_BY_LANG[lang]);
        Object.assign(translations[lang], CROP_BY_LANG[lang] || {});
        Object.assign(translations[lang], MARKET_BY_LANG[lang] || {});
    });

    function translateKey(key, fallback, lang) {
        const activeLang = lang || localStorage.getItem('preferred_language') || 'en';
        const langMap = translations[activeLang] || {};
        const enMap = translations.en || {};
        return langMap[key] || enMap[key] || fallback || key;
    }

    window.marketPulseT = translateKey;

    window.updateLanguage = function updateLanguageWithFallback(lang) {
        const selectedLang = translations[lang] ? lang : 'en';
        localStorage.setItem('preferred_language', selectedLang);

        document.querySelectorAll('[data-i18n]').forEach((element) => {
            const key = element.getAttribute('data-i18n');
            const value = translateKey(key, null, selectedLang);
            if (!value) {
                return;
            }

            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = value;
            } else {
                element.innerText = value;
            }
        });

        const selector = document.getElementById('language-selector');
        if (selector) {
            selector.value = selectedLang;
        }

        document.documentElement.setAttribute('lang', selectedLang);
        document.dispatchEvent(new CustomEvent('marketpulse:language-changed', { detail: { lang: selectedLang } }));
    };
})();
