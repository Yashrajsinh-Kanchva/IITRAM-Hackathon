(function (global) {
    'use strict';

    const CATEGORY_DEFAULTS = {
        vegetable: '/buyer/images/placeholders/vegetables-default.jpg',
        fruit: '/buyer/images/placeholders/fruits-default.jpg',
        grain: '/buyer/images/placeholders/grains-default.jpg',
        pulse: '/buyer/images/placeholders/pulses-default.jpg',
        spice: '/buyer/images/placeholders/spices-default.jpg',
        cash_crop: '/buyer/images/placeholders/farm-default.jpg',
        dairy: '/buyer/images/placeholders/farm-default.jpg',
        honey: '/buyer/images/placeholders/farm-default.jpg',
        farm: '/buyer/images/placeholders/farm-default.jpg',
    };

    const CATEGORY_ALIASES = {
        vegetables: 'vegetable',
        vegetable: 'vegetable',
        fruits: 'fruit',
        fruit: 'fruit',
        grains: 'grain',
        grain: 'grain',
        cereals: 'grain',
        cereal: 'grain',
        pulses: 'pulse',
        pulse: 'pulse',
        dal: 'pulse',
        lentils: 'pulse',
        lentil: 'pulse',
        legumes: 'pulse',
        legume: 'pulse',
        spices: 'spice',
        spice: 'spice',
        cashcrop: 'cash_crop',
        'cash crop': 'cash_crop',
        'cash-crop': 'cash_crop',
        dairy: 'dairy',
        honey: 'honey',
        all: 'farm',
        farm: 'farm',
    };

    const CROP_QUERY_MAP = {
        tomato: 'tomato,vegetable,farm',
        potato: 'potato,vegetable,farm',
        onion: 'onion,vegetable,farm',
        brinjal: 'brinjal,eggplant,farm',
        cauliflower: 'cauliflower,vegetable,farm',
        cabbage: 'cabbage,vegetable,farm',
        carrot: 'carrot,vegetable,farm',
        spinach: 'spinach,leafy,vegetable',
        peas: 'green peas,vegetable,farm',
        cucumber: 'cucumber,vegetable,farm',
        'bitter gourd': 'bitter gourd,vegetable,farm',
        'bottle gourd': 'bottle gourd,vegetable,farm',
        capsicum: 'capsicum,bell pepper,vegetable',
        garlic: 'garlic,vegetable,farm',
        ginger: 'ginger,root,farm',
        okra: 'okra,ladyfinger,farm',
        radish: 'radish,vegetable,farm',
        beetroot: 'beetroot,vegetable,farm',

        mango: 'mango,fruit,farm',
        banana: 'banana,fruit,farm',
        apple: 'apple,fruit,farm',
        grapes: 'grapes,fruit,farm',
        watermelon: 'watermelon,fruit,farm',
        papaya: 'papaya,fruit,farm',
        pomegranate: 'pomegranate,fruit,farm',
        guava: 'guava,fruit,farm',
        lemon: 'lemon,citrus,fruit',
        orange: 'orange,citrus,fruit',
        pineapple: 'pineapple,fruit,farm',
        strawberry: 'strawberry,fruit,farm',
        coconut: 'coconut,farm,fruit',
        chikoo: 'chikoo,sapota,fruit',

        wheat: 'wheat,grain,field',
        rice: 'rice,paddy,grain,field',
        barley: 'barley,grain,field',
        maize: 'maize,corn,grain,field',
        corn: 'corn,maize,grain,field',
        jowar: 'jowar,sorghum,grain',
        bajra: 'bajra,pearl millet,grain',
        ragi: 'ragi,finger millet,grain',
        oats: 'oats,grain,field',

        lentils: 'lentils,dal,pulses',
        chickpeas: 'chickpeas,chana,pulses',
        moong: 'moong,green gram,pulses',
        urad: 'urad,black gram,pulses',
        toor: 'toor dal,pigeon pea,pulses',
        rajma: 'rajma,kidney beans,pulses',
        soybean: 'soybean,pulses,farm',

        turmeric: 'turmeric,spice,farm',
        chilli: 'red chilli,spice,farm',
        coriander: 'coriander,spice,seed',
        cumin: 'cumin,jeera,spice',
        pepper: 'black pepper,spice',
        cardamom: 'cardamom,elaichi,spice',
        mustard: 'mustard,spice,seed',
        fenugreek: 'fenugreek,methi,spice',

        cotton: 'cotton,cash crop,farm',
        sugarcane: 'sugarcane,cash crop,farm',
        groundnut: 'groundnut,peanut,crop',
        sunflower: 'sunflower,cash crop,farm',
        jute: 'jute,cash crop,farm',
    };

    const CROP_ALIASES = {
        tomatoes: 'tomato',
        onion: 'onion',
        onions: 'onion',
        potatoes: 'potato',
        eggplant: 'brinjal',
        aubergine: 'brinjal',
        brinjal: 'brinjal',
        'lady finger': 'okra',
        ladyfinger: 'okra',
        bhindi: 'okra',
        lauki: 'bottle gourd',
        karela: 'bitter gourd',
        okra: 'okra',
        mirchi: 'chilli',
        chili: 'chilli',
        chillies: 'chilli',
        chilies: 'chilli',
        dal: 'lentils',
        chana: 'chickpeas',
        'kabuli chana': 'chickpeas',
        'chick pea': 'chickpeas',
        'chick peas': 'chickpeas',
        arhar: 'toor',
        'toor dal': 'toor',
        'pigeon pea': 'toor',
        masoor: 'lentils',
        'red lentil': 'lentils',
        'black gram': 'urad',
        'green gram': 'moong',
        'kidney beans': 'rajma',
        jeera: 'cumin',
        methi: 'fenugreek',
        sapota: 'chikoo',
        sorghum: 'jowar',
        millet: 'bajra',
        'finger millet': 'ragi',
        corn: 'maize',
        'sweet corn': 'maize',
        peanut: 'groundnut',
        peanuts: 'groundnut',
    };

    const CROP_KEYS = Object.keys(CROP_QUERY_MAP).sort((a, b) => b.length - a.length);
    const ALIAS_KEYS = Object.keys(CROP_ALIASES).sort((a, b) => b.length - a.length);

    function normalizeText(value) {
        return String(value || '')
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function normalizeImageCategory(category) {
        const normalized = normalizeText(category);
        return CATEGORY_ALIASES[normalized] || normalized || 'farm';
    }

    function makeUnsplashUrl(query) {
        return `https://source.unsplash.com/400x300/?${encodeURIComponent(query)}`;
    }

    function findCanonicalCrop(cropName) {
        const text = normalizeText(cropName);
        if (!text) return '';

        for (const alias of ALIAS_KEYS) {
            if (text.includes(alias)) {
                return CROP_ALIASES[alias];
            }
        }

        for (const key of CROP_KEYS) {
            if (text.includes(key)) {
                return key;
            }
        }

        return '';
    }

    function getCategoryFallbackImage(category) {
        const normalizedCategory = normalizeImageCategory(category);
        return CATEGORY_DEFAULTS[normalizedCategory] || CATEGORY_DEFAULTS.farm;
    }

    function getCropImage(cropName, category) {
        const canonical = findCanonicalCrop(cropName);
        if (canonical && CROP_QUERY_MAP[canonical]) {
            return makeUnsplashUrl(CROP_QUERY_MAP[canonical]);
        }

        return getCategoryFallbackImage(category);
    }

    global.normalizeImageCategory = normalizeImageCategory;
    global.getCategoryFallbackImage = getCategoryFallbackImage;
    global.getCropImage = getCropImage;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            normalizeImageCategory,
            getCategoryFallbackImage,
            getCropImage,
        };
    }
})(typeof window !== 'undefined' ? window : globalThis);
