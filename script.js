const state = {
    language: localStorage.getItem("language") || "id",
    dark: localStorage.getItem("darkMode") === "true",
    products: [],
    categories: [],
    currentCategory: "",
    currentSubcategory: ""
};


const translations = {

    id: {

        brand: "Asisten Belanja",

        nav_categories: "Kategori",
        nav_products: "Produk",
        nav_ai: "Asisten AI",

        hero_eyebrow: "BELANJA LEBIH CERDAS",

        hero_title:
            "Temukan produk yang tepat dengan mudah.",

        hero_desc:
            "Jelajahi berbagai kategori, cari produk sesuai kebutuhan, dan gunakan Asisten AI untuk membantu menentukan pilihan.",

        search_placeholder:
            "Cari produk...",

        search_button:
            "Cari",

        categories_eyebrow:
            "KATEGORI",

        categories_title:
            "Jelajahi kategori",

        products_eyebrow:
            "PRODUK",

        products_title:
            "Produk pilihan",

        sort_default:
            "Urutan",

        sort_low:
            "Harga terendah",

        sort_high:
            "Harga tertinggi",

        min_price:
            "Minimum",

        max_price:
            "Maksimum",

        filter_button:
            "Saring",

        ai_eyebrow:
            "ASISTEN AI",

        assistant_title:
            "Bingung memilih produk?",

        assistant_desc:
            "Jelaskan kebutuhan dan anggaran Anda. Asisten AI akan membantu berdasarkan produk yang tersedia.",

        assistant_welcome:
            "Halo. Jelaskan produk yang sedang Anda cari.",

        chat_placeholder:
            "Contoh: Saya mencari mouse untuk bekerja...",

        send_button:
            "Kirim",

        found:
            "produk ditemukan",

        empty:
            "Belum ada produk yang sesuai dengan pencarian Anda.",

        detail_category:
            "Kategori",

        detail_marketplace:
            "Tempat pembelian",

        buy:
            "Lihat Produk",

        test:
            "Belum tersedia",

        loading:
            "Sedang menganalisis produk...",

        error:
            "Maaf, terjadi kesalahan saat menghubungkan ke Asisten AI.",

        footer_text:
            "Asisten belanja untuk membantu Anda menemukan produk yang sesuai."
    },


    en: {

        brand: "Shopping Assistant",

        nav_categories: "Categories",
        nav_products: "Products",
        nav_ai: "AI Assistant",

        hero_eyebrow: "SMARTER SHOPPING",

        hero_title:
            "Find the right products more easily.",

        hero_desc:
            "Explore categories, search products based on your needs, and use AI Assistant to help make better choices.",

        search_placeholder:
            "Search products...",

        search_button:
            "Search",

        categories_eyebrow:
            "CATEGORIES",

        categories_title:
            "Explore categories",

        products_eyebrow:
            "PRODUCTS",

        products_title:
            "Featured products",

        sort_default:
            "Sort",

        sort_low:
            "Lowest price",

        sort_high:
            "Highest price",

        min_price:
            "Minimum",

        max_price:
            "Maximum",

        filter_button:
            "Filter",

        ai_eyebrow:
            "AI ASSISTANT",

        assistant_title:
            "Need help choosing?",

        assistant_desc:
            "Describe your needs and budget. AI Assistant will help based on available products.",

        assistant_welcome:
            "Hello. Tell me what product you are looking for.",

        chat_placeholder:
            "Example: I am looking for a mouse for work...",

        send_button:
            "Send",

        found:
            "products found",

        empty:
            "No products match your search.",

        detail_category:
            "Category",

        detail_marketplace:
            "Marketplace",

        buy:
            "View Product",

        test:
            "Unavailable",

        loading:
            "Analyzing available products...",

        error:
            "Sorry, an error occurred while connecting to AI Assistant.",

        footer_text:
            "A shopping assistant to help you discover suitable products."
    }
};


function t(key) {
    return translations[state.language][key] || key;
}


function applyTranslations() {

    const dict = translations[state.language];

    document
        .querySelectorAll("[data-i18n]")
        .forEach(element => {

            const key = element.dataset.i18n;

            if (dict[key]) {
                element.textContent = dict[key];
            }
        });


    document
        .querySelectorAll("[data-i18n-placeholder]")
        .forEach(element => {

            const key =
                element.dataset.i18nPlaceholder;

            if (dict[key]) {
                element.placeholder = dict[key];
            }
        });


    document.getElementById("brandText").textContent =
        dict.brand;

    document.getElementById("footerBrand").textContent =
        dict.brand;

    document.getElementById("languageBtn").textContent =
        state.language === "id"
            ? "EN"
            : "ID";

    document.documentElement.lang =
        state.language;
}


function applyTheme() {

    document.body.classList.toggle(
        "dark",
        state.dark
    );
}


function formatRupiah(value) {

    return new Intl.NumberFormat(
        "id-ID",
        {
            style: "currency",
            currency: "IDR",
            maximumFractionDigits: 0
        }
    ).format(
        Number(value) || 0
    );
}


function getCategoryIcon(category) {

    const icons = {

        "Dapur": "🍳",
        "Kamar Tidur": "🛏️",
        "Kamar Mandi": "🚿",
        "Ruang Tamu": "🛋️",
        "Kebersihan Rumah": "🧹",
        "Tools & Perkakas": "🔧",
        "Taman & Outdoor": "🌿",
        "Elektronik Rumah": "⚡",
        "Otomotif": "🚗",
        "Gadget & Elektronik": "💻",
        "Fashion": "👕",
        "Olahraga": "🏃",
        "Sekolah & Kantor": "🎒",
        "Bayi & Anak": "🧸",
        "Hewan Peliharaan": "🐾",
        "Kecantikan & Perawatan": "✨",
        "Makanan & Minuman": "🍽️",
        "Travel": "🧳",
        "Hobi & Hiburan": "🎮",
        "Hadiah & Lainnya": "🎁"
    };

    return icons[category] || "◉";
}


function categoryLabel(category) {

    if (state.language === "id") {
        return category.nama;
    }

    return category.nama_en;
}


function findCategory(name) {

    return state.categories.find(
        category =>
            category.nama === name
    );
}


function productCategoryLabel(name) {

    const category =
        findCategory(name);

    if (!category) {
        return name || "";
    }

    return categoryLabel(category);
}


async function loadCategories() {

    const response =
        await fetch("/api/categories");

    state.categories =
        await response.json();

    renderCategories();
}


function renderCategories() {

    const grid =
        document.getElementById(
            "categoryGrid"
        );

    grid.innerHTML = "";

    state.categories.forEach(category => {

        const card =
            document.createElement("div");

        card.className =
            "category-card";

        if (
            state.currentCategory ===
            category.nama
        ) {
            card.classList.add("active");
        }

        card.innerHTML = `

            <div class="category-icon">
                ${category.icon || getCategoryIcon(category.nama)}
            </div>

            <div class="category-name">
                ${categoryLabel(category)}
            </div>

            <div class="category-subtitle">
                ${state.language === "id"
                    ? "Lihat produk"
                    : "View products"}
            </div>
        `;

        card.addEventListener(
            "click",
            () => {

                state.currentCategory =
                    category.nama;

                document.getElementById(
                    "searchInput"
                ).value = "";

                renderCategories();

                loadProducts();

                document.getElementById(
                    "produk"
                ).scrollIntoView({
                    behavior: "smooth"
                });
            }
        );

        grid.appendChild(card);
    });
}



function updateSubcategoryOptions() {
    const select = document.getElementById("subcategorySelect");
    if (!select) return;

    const products = state.products || [];
    const category = state.currentCategory || "";

    const values = [...new Set(
        products
            .filter(product => !category || product.kategori === category)
            .map(product => product.subkategori)
            .filter(Boolean)
    )];

    const current = select.value;

    select.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent =
        state.language === "en"
            ? "Subcategory"
            : "Subkategori";

    select.appendChild(allOption);

    values.forEach(value => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });

    if (values.includes(current)) {
        select.value = current;
    } else {
        select.value = "";
        state.currentSubcategory = "";
    }
}


function rankProducts(products, query = "") {
    const q = String(query || "").toLowerCase().trim();

    return [...products].sort((a, b) => {
        if (!q) {
            return (Number(b.rating) || 0) - (Number(a.rating) || 0);
        }

        function score(product) {
            let value = 0;

            const name = String(product.nama || "").toLowerCase();
            const nameEn = String(product.nama_en || "").toLowerCase();
            const desc = String(product.deskripsi || "").toLowerCase();
            const descEn = String(product.deskripsi_en || "").toLowerCase();
            const category = String(product.kategori || "").toLowerCase();
            const subcategory = String(product.subkategori || "").toLowerCase();

            if (name === q || nameEn === q) value += 100;
            if (name.includes(q) || nameEn.includes(q)) value += 60;
            if (subcategory.includes(q)) value += 40;
            if (category.includes(q)) value += 30;
            if (desc.includes(q) || descEn.includes(q)) value += 15;

            value += (Number(product.rating) || 0) * 2;

            return value;
        }

        return score(b) - score(a);
    });
}

function reorderProductSection(query = "") {
    const productSection = document.getElementById("produk");
    const categoryGrid = document.getElementById("categoryGrid");

    if (!productSection || !categoryGrid) {
        return;
    }

    const categorySection = categoryGrid.closest("section");

    if (!categorySection || !categorySection.parentNode) {
        return;
    }

    const parent = categorySection.parentNode;
    const hasQuery = String(query || "").trim() !== "";

    if (hasQuery) {
        parent.insertBefore(productSection, categorySection);
    } else {
        parent.insertBefore(categorySection, productSection);
    }
}


async function loadProducts(options = {}) {

    const query =
        options.query !== undefined
            ? options.query
            : document.getElementById("searchInput").value.trim();

    const min =
        options.min !== undefined
            ? options.min
            : document.getElementById("minPrice").value;

    const max =
        options.max !== undefined
            ? options.max
            : document.getElementById("maxPrice").value;

    const sort =
        document.getElementById("sortSelect").value;

    try {

        const response =
            await fetch("/api/products");

        if (!response.ok) {
            throw new Error("Gagal mengambil produk.");
        }

        let products =
            await response.json();

        const q =
            String(query || "").toLowerCase().trim();

        if (q) {
            products =
                products.filter(product => {

                    const text = [
                        product.nama,
                        product.nama_en,
                        product.deskripsi,
                        product.deskripsi_en,
                        product.kategori,
                        product.subkategori,
                        product.marketplace
                    ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();

                    return text.includes(q) || (q.split(/\s+/)[0] && (String(product.nama || "").toLowerCase().includes(q.split(/\s+/)[0]) || String(product.nama_en || "").toLowerCase().includes(q.split(/\s+/)[0])));
                });
        }

        if (state.currentCategory) {
            products =
                products.filter(product =>
                    product.kategori === state.currentCategory
                );
        }

        if (state.currentSubcategory) {
            products =
                products.filter(product =>
                    product.subkategori === state.currentSubcategory
                );
        }

        if (min) {
            products =
                products.filter(product =>
                    Number(product.harga) >= Number(min)
                );
        }

        if (max) {
            products =
                products.filter(product =>
                    Number(product.harga) <= Number(max)
                );
        }

        if (sort !== "default") {

            products.sort((a, b) => {

                const pa =
                    Number(a.harga) || 0;

                const pb =
                    Number(b.harga) || 0;

                return sort === "asc"
                    ? pa - pb
                    : pb - pa;
            });
        }

        state.products = products;

        renderProducts();
        reorderProductSection(query);

    } catch (error) {

        console.error("loadProducts error:", error);

        state.products = [];

        renderProducts();
    }
}

function productName(product) {

    if (
        state.language === "en" &&
        product.nama_en
    ) {
        return product.nama_en;
    }

    return product.nama;
}


function productDescription(product) {

    if (
        state.language === "en" &&
        product.deskripsi_en
    ) {
        return product.deskripsi_en;
    }

    return product.deskripsi || "";
}


function renderProducts() {

    const grid =
        document.getElementById(
            "productGrid"
        );

    const resultText =
        document.getElementById(
            "productResultText"
        );

    grid.innerHTML = "";

    const count =
        state.products.length;

    resultText.textContent =
        `${count} ${t("found")}`;


    if (!count) {

        grid.innerHTML = `
            <div class="empty-state">
                ${t("empty")}
            </div>
        `;

        return;
    }


    state.products.forEach(product => {

        const card =
            document.createElement("article");

        card.className =
            "product-card";


        const marketplace =
            product.marketplace ||
            product.jenis ||
            "";


        const hasLink =
            product.link &&
            !String(
                product.link
            ).includes("contoh.com");


        card.innerHTML = `

            <div class="product-visual">
                ${getCategoryIcon(product.kategori)}
            </div>

            <div class="product-content">

                <div class="product-category">
                    ${productCategoryLabel(product.kategori)}
                </div>

                <h3 class="product-name">
                    ${productName(product)}
                </h3>

                <div class="product-description">
                    ${productDescription(product)}
                </div>

                <div class="product-price">
                    ${formatRupiah(product.harga)}
                </div>

                <div class="product-actions">

                    ${
                        hasLink
                            ? `
                                <a
                                    href="${product.link}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    ${marketplace ? ((state.language === "en" ? "View on " : "Lihat di ") + marketplace) : t("buy")}
                                </a>
                              `
                            : `
                                <button
                                    type="button"
                                    disabled
                                    title="${t("test")}"
                                >
                                    ${t("test")}
                                </button>
                              `
                    }

                    <button
                        type="button"
                        onclick="showProductDetail(${product.id})"
                    >
                        +
                    </button>

                </div>

            </div>
        `;

        grid.appendChild(card);
    });
}


async function showProductDetail(id) {

    const response =
        await fetch(
            `/api/products/${id}`
        );

    if (!response.ok) {
        return;
    }

    const product =
        await response.json();

    const message =
        state.language === "id"

            ? `${productName(product)}
${formatRupiah(product.harga)}
${productDescription(product)}
${t("detail_category")}: ${productCategoryLabel(product.kategori)}
${t("detail_marketplace")}: ${product.marketplace || "-"}`

            : `${productName(product)}
${formatRupiah(product.harga)}
${productDescription(product)}
${t("detail_category")}: ${productCategoryLabel(product.kategori)}
${t("detail_marketplace")}: ${product.marketplace || "-"}`;

    alert(message);
}


async function sendChat() {

    const input =
        document.getElementById(
            "chatInput"
        );

    const messages =
        document.getElementById(
            "chatMessages"
        );

    const button =
        document.getElementById(
            "chatBtn"
        );

    const message =
        input.value.trim();

    if (!message) {
        return;
    }


    const userBubble =
        document.createElement("div");

    userBubble.className =
        "chat-message user-message";

    userBubble.textContent =
        message;

    messages.appendChild(
        userBubble
    );

    input.value = "";

    button.disabled = true;


    const loading =
        document.createElement("div");

    loading.className =
        "chat-message assistant-message";

    loading.textContent =
        t("loading");

    messages.appendChild(
        loading
    );

    messages.scrollTop =
        messages.scrollHeight;


    try {

        const response =
            await fetch(
                "/api/shopping-assistant",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message,
                        language:
                            state.language
                    })
                }
            );


        const data =
            await response.json();

        loading.textContent =
            data.reply || "";


        if (
            Array.isArray(
                data.products
            ) &&
            data.products.length
        ) {

            const productList =
                document.createElement(
                    "div"
                );

            productList.className =
                "chat-product-list";


            data.products
                .forEach(product => {

                    const item =
                        document.createElement(
                            "div"
                        );

                    item.className =
                        "chat-product";

                    item.innerHTML = `

                        <strong>
                            ${productName(product)}
                        </strong>

                        <span>
                            ${formatRupiah(product.harga)}
                        </span>

                        <span>
                            ${productCategoryLabel(product.kategori)}
                        </span>
                    `;

                    productList.appendChild(
                        item
                    );
                });


            loading.appendChild(
                productList
            );
        }

    } catch (error) {

        loading.textContent =
            t("error");
    }


    button.disabled = false;

    messages.scrollTop =
        messages.scrollHeight;
}


async function runSearch() {
    const input = document.getElementById("searchInput");

    if (!input) {
        return;
    }

    state.currentCategory = "";

    renderCategories();

    await loadProducts({
        query: input.value.trim()
    });
}


document
    .getElementById("searchBtn")
    .addEventListener("click", runSearch);


document
    .getElementById("searchInput")
    .addEventListener(
        "keydown",
        event => {
            if (event.key === "Enter") {
                event.preventDefault();
                runSearch();
            }
        }
    );


document
    .getElementById("filterBtn")
    .addEventListener(
        "click",
        () => loadProducts()
    );


document
    .getElementById("sortSelect")
    .addEventListener(
        "change",
        () => loadProducts()
    );


document
    .getElementById("chatBtn")
    .addEventListener(
        "click",
        sendChat
    );


document
    .getElementById("chatInput")
    .addEventListener(
        "keydown",
        event => {

            if (event.key === "Enter") {
                sendChat();
            }
        }
    );


document
    .getElementById("languageBtn")
    .addEventListener(
        "click",
        () => {

            state.language =
                state.language === "id"
                    ? "en"
                    : "id";

            localStorage.setItem(
                "language",
                state.language
            );

            applyTranslations();

            renderCategories();

            renderProducts();
        }
    );


document
    .getElementById("themeBtn")
    .addEventListener(
        "click",
        () => {

            state.dark =
                !state.dark;

            localStorage.setItem(
                "darkMode",
                state.dark
            );

            applyTheme();
        }
    );


async function init() {

    applyTranslations();

    applyTheme();

    await loadCategories();

    await loadProducts();
}


init();










function getFavorites(){try{return JSON.parse(localStorage.getItem("favoriteProducts")||"[]")}catch{return[]}} function saveFavorites(items){localStorage.setItem("favoriteProducts",JSON.stringify(items))} function toggleFavorite(id,button){let items=getFavorites();id=Number(id);if(items.includes(id)){items=items.filter(x=>x!==id);button.classList.remove("active");button.textContent="☆"}else{items.push(id);button.classList.add("active");button.textContent="★"}saveFavorites(items)} function updateFavoriteButtons(){document.querySelectorAll(".product-card").forEach(card=>{if(card.querySelector(".favorite-btn"))return;const plus=card.querySelector(".product-actions button:not([disabled])");if(!plus)return;const idMatch=(plus.getAttribute("onclick")||"").match(/\d+/);if(!idMatch)return;const id=Number(idMatch[0]);const button=document.createElement("button");button.type="button";button.className="favorite-btn";button.textContent=getFavorites().includes(id)?"★":"☆";if(getFavorites().includes(id))button.classList.add("active");button.onclick=()=>toggleFavorite(id,button);card.querySelector(".product-actions").prepend(button)})} const favoriteObserver=new MutationObserver(()=>updateFavoriteButtons()); document.addEventListener("DOMContentLoaded",()=>updateFavoriteButtons()); const productGrid=document.getElementById("productGrid"); if(productGrid)favoriteObserver.observe(productGrid,{childList:true,subtree:true});
(()=>{function stage62Get(){try{return JSON.parse(localStorage.getItem("searchHistory")||"[]")}catch{return[]}}function stage62Save(q){q=String(q||"").trim();if(!q)return;let h=stage62Get().filter(x=>String(x).toLowerCase()!==q.toLowerCase());h.unshift(q);localStorage.setItem("searchHistory",JSON.stringify(h.slice(0,10)))}function stage62Render(){const i=document.getElementById("searchInput");if(!i||!i.parentElement)return;let b=document.getElementById("stage62History");if(b)b.remove();const h=stage62Get();if(!h.length)return;b=document.createElement("div");b.id="stage62History";b.className="search-history-box";b.innerHTML=`<span class="search-history-title">${state.language==="en"?"Recent searches":"Riwayat Pencarian"}</span>`+h.map(q=>`<button type="button" class="search-history-item">${q}</button>`).join("")+`<button type="button" class="search-history-clear">${state.language==="en"?"Clear":"Hapus"}</button>`;b.querySelectorAll(".search-history-item").forEach((x,n)=>x.addEventListener("click",()=>{i.value=h[n];if(typeof loadProducts==="function")loadProducts({query:h[n]});stage62Render()}));b.querySelector(".search-history-clear").addEventListener("click",()=>{localStorage.removeItem("searchHistory");stage62Render()});i.parentElement.insertAdjacentElement("afterend",b)}function stage62Run(){const i=document.getElementById("searchInput");if(i){stage62Save(i.value);setTimeout(stage62Render,100)}}document.addEventListener("DOMContentLoaded",()=>{const i=document.getElementById("searchInput");if(!i)return;i.addEventListener("keydown",e=>{if(e.key==="Enter")stage62Run()});const btn=i.closest("form")?.querySelector("button")||i.parentElement.querySelector("button");if(btn)btn.addEventListener("click",stage62Run);stage62Render()})})()

function getUserPreferences(){try{return JSON.parse(localStorage.getItem("userPreferences")||"{}")}catch{return{}}} function saveUserPreference(key,value){const p=getUserPreferences();p[key]=value;localStorage.setItem("userPreferences",JSON.stringify(p))} function getPreferredCategory(){return getUserPreferences().category||""} function setPreferredCategory(category){saveUserPreference("category",category)}
function stage62AlignClear(){const h=document.querySelector(".search-history-box"),c=document.querySelector(".search-history-clear");if(!h||!c)return;h.style.position="relative";c.style.position="static";c.style.left="auto";c.style.top="auto"}window.addEventListener("load",()=>setTimeout(stage62AlignClear,200));window.addEventListener("resize",stage62AlignClear);new MutationObserver(()=>setTimeout(stage62AlignClear,50)).observe(document.body,{childList:true,subtree:true});
function stage62AlignClear(){const h=document.querySelector(".search-history-box"),c=document.querySelector(".search-history-clear");if(!h||!c)return;h.style.position="relative";c.style.position="static";c.style.left="auto";c.style.top="auto"}window.addEventListener("load",()=>setTimeout(stage62AlignClear,200));window.addEventListener("resize",stage62AlignClear);new MutationObserver(()=>setTimeout(stage62AlignClear,50)).observe(document.body,{childList:true,subtree:true});
