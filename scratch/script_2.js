
  const KEY_ITEMS = "breathe:items";
  const KEY_IS_OPEN = "breathe:isOpen";
  const KEY_SLIDE_INDEX = "breathe:currentSlideIndex";

  let LOCATIONS = [];

  let currentLocationIndex = 0;
  let isReviewMode = false;
  let selectedReviewLocation = "";
  let selectedReviewDate = "";
  let isGenerating = false;
  let isShuffling = false;
  let lastHomeGlobeIndex = 0;

  function todayLabel() {
    const d = new Date();
    const week = ["日","一","二","三","四","五","六"][d.getDay()];
    return d.getFullYear() + " 年 " + (d.getMonth()+1) + " 月 " + d.getDate() + " 日 · 星期" + week;
  }

  function todayLabelShort() {
    const d = new Date();
    return d.getFullYear() + "." + String(d.getMonth() + 1).padStart(2, '0') + "." + String(d.getDate()).padStart(2, '0');
  }

  function formatTime(d) {
    return String(d.getHours()).padStart(2, '0') + ":" + String(d.getMinutes()).padStart(2, '0');
  }

  function show(id) {
    ["gate","feed","fail"].forEach(s => {
      document.getElementById(s).classList.toggle("hidden", s !== id);
    });
  }

  // --- Location Switcher Logic ---
  function applyLocationSettings(index, isImmediate = false, skipGlobe = false) {
    const loc = LOCATIONS[index];
    const wrapper = document.getElementById("windowWrapper");
    if (!loc) return;
    
    // Remove old location classes
    LOCATIONS.forEach(l => wrapper.classList.remove(l.locClass));
    // Add new location class
    wrapper.classList.add(loc.locClass);
    
    // Update badge label
    document.getElementById("locBadge").textContent = "📍 " + loc.name;

    // 更新已探访状态标签
    try {
      const history = getHistory();
      const isVisited = history.some(entry => entry.location === loc.name);
      const statusTag = document.getElementById("visitStatusTag");
      if (statusTag) {
        if (isVisited) {
          statusTag.textContent = "✓";
          statusTag.className = "loc-stamp-seal visited";
          statusTag.setAttribute("data-tooltip", "已留下手账印记");
        } else {
          statusTag.textContent = "";
          statusTag.className = "loc-stamp-seal unvisited";
          statusTag.setAttribute("data-tooltip", "待开启探索");
        }
      }
    } catch (e) {}

    // 同步更新首页半球位置（换窗动画期间由 shuffleLocation 手动接管，跳过）
    if (!skipGlobe) {
      try {
        updateHomeGlobe(index, isImmediate);
      } catch(e) {}
    }
  }

  function shuffleLocation() {
    const wrapper = document.getElementById("windowWrapper");
    const isOpen = localStorage.getItem(KEY_IS_OPEN) === "true";
    if (isOpen || isGenerating || isShuffling || wrapper.classList.contains("zoomed")) return;

    isShuffling = true;

    const locBadgeWrapper = document.getElementById("locBadgeWrapper");
    const btnGroup = document.getElementById("btnGroup");
    const gateTitle = document.getElementById("gateTitle");
    const gateSub = document.getElementById("gateSub");
    const openBtn = document.getElementById("openBtn");
    const shuffleBtn = document.getElementById("shuffleBtn");
    const globeWrapper = document.getElementById("homeGlobeWrapper");

    if (openBtn) openBtn.disabled = true;
    if (shuffleBtn) shuffleBtn.disabled = true;

    // 坍缩锚点 = 升起后地球的视觉中心，所有元素仿佛被吸入地球
    const centerX = window.innerWidth / 2;
    const globeCenterY = window.innerHeight * 0.6;   // 升起时球心落在视口 60% 处，整体略偏下更稳重
    const RAISED_ZOOM = 1.15;   // 升起为整球时的地图缩放（露出更多大陆，转动更有“地球感”）

    // 将某元素朝中心锚点坍缩为一点
    function collapseTo(el, extraY) {
      if (!el) return;
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      el.style.transition = "transform 1.3s cubic-bezier(0.6, 0, 0.2, 1), opacity 0.85s ease-in";
      el.style.transform = `translate(${centerX - cx}px, ${globeCenterY - cy + (extraY || 0)}px) scale(0.02)`;
      el.style.opacity = "0";
    }

    // ═══ Phase A: 所有元素坍缩成点 + 地球完整升起为整球 (0 → 1.5s) ═══
    collapseTo(wrapper, 0);
    collapseTo(locBadgeWrapper, 0);
    collapseTo(btnGroup, -18);
    if (btnGroup) btnGroup.style.pointerEvents = "none";
    if (gateTitle) { gateTitle.style.transition = "opacity 0.55s ease"; gateTitle.style.opacity = "0"; }
    if (gateSub)   { gateSub.style.transition = "opacity 0.55s ease"; gateSub.style.opacity = "0"; }

    // 把球心从屏幕下方抬到 globeCenterY，使整个圆球完整浮现
    const raiseY = globeCenterY - window.innerHeight - 120;
    if (globeWrapper) {
      globeWrapper.style.transition = "transform 1.5s cubic-bezier(0.25, 1, 0.5, 1)";
      globeWrapper.style.transform = `translateX(-50%) translateY(${raiseY}px)`;
    }

    // 当前城市随升起平移到球心，并把地图缩放到整球视角
    panGlobeToCity(LOCATIONS[currentLocationIndex], 320, 320, RAISED_ZOOM,
                   "transform 1.5s cubic-bezier(0.25, 1, 0.5, 1)");
    const pin0 = document.getElementById("homeGlobePin");
    if (pin0) { pin0.style.transition = "opacity 0.6s ease"; pin0.style.opacity = "1"; }

    // ═══ Phase B: 整球转动，从当前城市滚向目的地 (1.5s → 3.7s) ═══
    setTimeout(() => {
      // 先让旧红点【就地】淡出，淡出期间绝不移动它的坐标，避免“跳位闪烁”
      const pin = document.getElementById("homeGlobePin");
      if (pin) { pin.style.transition = "opacity 0.4s ease"; pin.style.opacity = "0"; }

      // 在所有可抽取城市(LOCATIONS 已过滤为 hasCustomImages 城市)中随机抽取，
      // 排除当前城市，保证每次都确实换到不同的一扇窗
      if (LOCATIONS.length > 1) {
        let nextIndex;
        do {
          nextIndex = Math.floor(Math.random() * LOCATIONS.length);
        } while (nextIndex === currentLocationIndex);
        currentLocationIndex = nextIndex;
      }
      try { localStorage.setItem("breathe:currentLocationIndex", currentLocationIndex); } catch (e) {}

      // 切换窗框主题与徽章（地球转动由本函数手动接管，故跳过其内置定位）
      applyLocationSettings(currentLocationIndex, true, true);

      // 等旧红点【完全】淡出后(>0.4s)，红点已不可见，此时再把它移到目的城市
      // 并启动地图平移——坐标跳变发生在透明状态下，肉眼无感
      setTimeout(() => {
        panGlobeToCity(LOCATIONS[currentLocationIndex], 320, 320, RAISED_ZOOM,
                       "transform 1.8s cubic-bezier(0.45, 0, 0.2, 1)");

        // 临近落点时，目的地红点在球心徐徐亮起
        setTimeout(() => {
          const p2 = document.getElementById("homeGlobePin");
          if (p2) { p2.style.transition = "opacity 0.8s ease"; p2.style.opacity = "1"; }
        }, 1150);
      }, 450);
    }, 1500);

    // ═══ Phase C: 地球放大着沉回底部，回到半球露出态 (3.9s → 5.2s) ═══
    setTimeout(() => {
      if (globeWrapper) {
        globeWrapper.style.transition = "transform 1.3s cubic-bezier(0.5, 0, 0.2, 1)";
        globeWrapper.style.transform = "translateX(-50%)";
      }
      panGlobeToCity(LOCATIONS[currentLocationIndex], 320, 180, 1.4,
                     "transform 1.3s cubic-bezier(0.5, 0, 0.2, 1)");
      lastHomeGlobeIndex = currentLocationIndex;
    }, 3900);

    // ═══ Phase D: 其余元素从中心一点缓缓重新展开 (5.2s → 6.6s) ═══
    setTimeout(() => {
      function expand(el, delay) {
        if (!el) return;
        el.style.transition = `transform 1.4s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s, opacity 0.9s ease-out ${delay}s`;
        el.style.transform = "translate(0, 0) scale(1)";
        el.style.opacity = "1";
      }
      expand(wrapper, 0);
      expand(locBadgeWrapper, 0.1);
      expand(btnGroup, 0.2);
      if (gateTitle) { gateTitle.style.transition = "opacity 1.2s ease-out 0.3s"; gateTitle.style.opacity = "1"; }
      if (gateSub)   { gateSub.style.transition = "opacity 1.2s ease-out 0.4s"; gateSub.style.opacity = "1"; }
    }, 5200);

    // ═══ Phase E: 动画收尾，清除行内样式 (6.8s) ═══
    setTimeout(() => {
      [wrapper, locBadgeWrapper, btnGroup, gateTitle, gateSub].forEach(el => {
        if (!el) return;
        el.style.transition = "";
        el.style.transform = "";
        el.style.opacity = "";
      });
      if (btnGroup) btnGroup.style.pointerEvents = "";
      if (globeWrapper) {
        globeWrapper.style.transition = "";
        globeWrapper.style.transform = "translateX(-50%)";
      }
      const pin = document.getElementById("homeGlobePin");
      if (pin) pin.style.transition = "";
      if (openBtn) openBtn.disabled = false;
      if (shuffleBtn) shuffleBtn.disabled = false;
      isShuffling = false;
    }, 6800);
  }


  // --- Drawer / History Logbook Logic ---
  let activeDrawerTab = "map"; // 默认展示地图视图

  function toggleDrawer(isOpen) {
    const drawer = document.getElementById("drawer");
    const overlay = document.getElementById("drawerOverlay");
    
    if (isOpen) {
      drawer.classList.add("open");
      overlay.classList.add("open");
      switchDrawerTab(activeDrawerTab);
    } else {
      drawer.classList.remove("open");
      overlay.classList.remove("open");
      const tooltip = document.getElementById("mapTooltip");
      if (tooltip) tooltip.style.opacity = "0";
    }
  }

  function switchDrawerTab(tab) {
    activeDrawerTab = tab;
    
    const tabMap = document.getElementById("tabMap");
    const tabStamps = document.getElementById("tabStamps");
    const mapView = document.getElementById("mapViewWrapper");
    const stampGrid = document.getElementById("stampGrid");
    const stampEmpty = document.getElementById("stampEmpty");
    const drawer = document.getElementById("drawer");
    
    if (tab === "map") {
      tabMap.classList.add("active");
      tabStamps.classList.remove("active");
      mapView.classList.remove("hidden");
      stampGrid.classList.add("hidden");
      stampEmpty.classList.add("hidden");
      drawer.classList.add("large-mode");
      
      const svgElement = document.querySelector("#worldMapContainer svg");
      if (!svgElement) {
        initWorldMap();
      } else {
        renderMapPins();
      }
    } else {
      tabMap.classList.remove("active");
      tabStamps.classList.add("active");
      mapView.classList.add("hidden");
      drawer.classList.remove("large-mode");
      
      renderTravelLog();
    }
  }

  // --- Homepage Hemi-Globe logic ---
  async function initHomeGlobe() {
    try {
      const response = await fetch("./assets/data/world-map.min.svg");
      if (!response.ok) throw new Error("地图文件加载失败");
      const svgText = await response.text();
      const container = document.getElementById("homeGlobeMap");
      if (container) {
        container.innerHTML = svgText;
        const svgElement = container.querySelector("svg");
        if (svgElement) {
          svgElement.setAttribute("width", "100%");
          svgElement.setAttribute("height", "100%");
          svgElement.setAttribute("preserveAspectRatio", "xMidYMid meet");
        }
        
        // 初始定位首页地球（立即执行，无动画）
        updateHomeGlobe(currentLocationIndex, true);
      }
    } catch(e) {
      console.error("加载首页地球地图失败:", e);
    }
  }

  /* ===== 坐标解析：彻底摆脱投影公式，改用国家 path 的几何中心 ===== */

  // 这张 world-map.min.svg 的 viewBox（非 0 起点，必须减偏移）
  const VB = { x: 30.767, y: 241.591, w: 784.077, h: 458.627 };
  // .home-globe-map 容器尺寸（见 CSS）
  const MAP_BOX = { w: 1200, h: 800 };

  // viewBox 坐标 → .home-globe-map 的 div 像素坐标
  // preserveAspectRatio="xMidYMid meet"：等比缩放取较小比例、居中留白
  function viewBoxToMapPx(vx, vy) {
    const scale = Math.min(MAP_BOX.w / VB.w, MAP_BOX.h / VB.h);
    const offsetX = (MAP_BOX.w - VB.w * scale) / 2;
    const offsetY = (MAP_BOX.h - VB.h * scale) / 2;
    return {
      x: (vx - VB.x) * scale + offsetX,
      y: (vy - VB.y) * scale + offsetY
    };
  }

  // 取某城市所属国家 path 的几何中心（viewBox 原始坐标）
  function getCityViewBoxXY(loc) {
    const code = (loc.countryCode || getCountryCode(loc.name) || "").toLowerCase();
    const svg = document.querySelector("#homeGlobeMap svg") || document.querySelector("#worldMapContainer svg");
    if (svg && code) {
      const el = svg.getElementById(code);
      if (el && el.getBBox) {
        try {
          const b = el.getBBox();
          return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
        } catch (e) { /* 未渲染完成时落空，走兜底 */ }
      }
    }
    return null;
  }

  // 解析城市在 home-globe-map 上的最终像素坐标
  function resolveCityMapPx(loc) {
    // 1) locations.json 手填 viewBox 坐标优先（大国如 cn/us/ca 建议手填，否则中心会落在国土正中）
    if (typeof loc.mapX === "number" && typeof loc.mapY === "number") {
      return viewBoxToMapPx(loc.mapX, loc.mapY);
    }
    // 2) 国家 path 几何中心
    const vb = getCityViewBoxXY(loc);
    if (vb) return viewBoxToMapPx(vb.x, vb.y);
    // 3) 兜底：老公式（坐标可能不准，仅防止崩溃）
    return { x: 2.220002 * loc.lng + 411.737295, y: -2.935935 * loc.lat + 533.594919 };
  }

  /* ===== 首页半球飞行定位 ===== */

  // 将地图平移/缩放，使某城市落到球面指定锚点 (tx,ty)；红点钉在该城市上随地图一起移动
  function panGlobeToCity(loc, tx, ty, zoom, mapTransition) {
    const mapEl = document.getElementById("homeGlobeMap");
    if (!mapEl || !loc) return null;
    const p = resolveCityMapPx(loc);
    let pin = document.getElementById("homeGlobePin");
    if (!pin) {
      pin = document.createElement("div");
      pin.id = "homeGlobePin";
      pin.className = "home-globe-pin";
      mapEl.appendChild(pin);
    }
    pin.style.setProperty('--stamp-color', loc.woodDark || '#d45d54');  // 红点跟随窗框深色，与窗户保持一致
    pin.style.left = `${p.x}px`;
    pin.style.top = `${p.y}px`;
    mapEl.style.transition = mapTransition || "";
    mapEl.style.transform = `translate(${tx - p.x * zoom}px, ${ty - p.y * zoom}px) scale(${zoom})`;
    return pin;
  }

  let homeGlobeTimeout = null;

  function updateHomeGlobe(index, isImmediate = false) {
    if (homeGlobeTimeout) {
      clearTimeout(homeGlobeTimeout);
      homeGlobeTimeout = null;
    }

    const loc = LOCATIONS[index];
    if (!loc) return;
    const mapEl = document.getElementById("homeGlobeMap");
    if (!mapEl) return;

    // —— 与 CSS 联动的几何常量（球径 D=640、露出 200）——
    const GX = 320;          // = D / 2 = 640 / 2，水平正中
    const GY = 180;          // 红点默认落点（球面纵坐标，越大越靠下）；须与 shuffle Phase C 落点保持一致
    const FINAL_ZOOM = 1.4;  // 球更大了，降落倍率略降，避免大陆撑爆露出区
    const MID_ZOOM   = 0.7;  // 起飞拉得更远，飞越感更足

    // 城市在地图上的最终像素坐标（已含投影校正）
    const p = resolveCityMapPx(loc);
    const x = p.x, y = p.y;

    // 创建 / 复用红点
    let pin = document.getElementById("homeGlobePin");
    if (!pin) {
      pin = document.createElement("div");
      pin.id = "homeGlobePin";
      pin.className = "home-globe-pin";
      mapEl.appendChild(pin);
    }

    if (isShuffling && !isImmediate) {
      // 开启滑动过渡，时间略微比起飞降落的总周期（4.0s）短一点点，使其平滑滑行到新位置
      pin.style.transition = "left 3.6s cubic-bezier(0.25, 1, 0.5, 1), top 3.6s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.8s ease";
    } else {
      pin.style.transition = "";
    }

    pin.style.setProperty('--stamp-color', loc.woodDark || '#d45d54');  // 红点跟随窗框深色，与窗户保持一致
    // 红点钉在城市像素位置，由地图 transform 带着一起飞
    pin.style.left = `${x}px`;
    pin.style.top  = `${y}px`;

    // origin 已是 0 0：城市 (x,y) 放大 s 倍后平移落到球面 (GX,GY)
    const finalTx = GX - x * FINAL_ZOOM;
    const finalTy = GY - y * FINAL_ZOOM;

    if (isImmediate) {
      mapEl.style.transition = "none";
      mapEl.style.transform = `translate(${finalTx}px, ${finalTy}px) scale(${FINAL_ZOOM})`;
      pin.style.opacity = "1";
      lastHomeGlobeIndex = index;
      return;
    }

    // 根据上一次的地点和这一次的目标点计算中点坐标，避免“拉回地图中心（南美洲附近）”的尴尬回环
    const sourceLoc = LOCATIONS[lastHomeGlobeIndex] || loc;
    const pSource = resolveCityMapPx(sourceLoc);
    const midX = (x + pSource.x) / 2;
    const midY = (y + pSource.y) / 2;

    // 记录本次定位点为下一次的起点
    lastHomeGlobeIndex = index;

    // 起飞：以两城几何中心拉远俯瞰，使用优雅舒缓的慢速曲线。如果是切换模式，红点做为载体保持清晰可见
    const midTx = GX - midX * MID_ZOOM;
    const midTy = GY - midY * MID_ZOOM;
    pin.style.opacity = isShuffling ? "0.9" : "0.25";
    mapEl.style.transition = "transform 1.8s cubic-bezier(0.25, 1, 0.5, 1)";
    mapEl.style.transform = `translate(${midTx}px, ${midTy}px) scale(${MID_ZOOM})`;

    // 降落：平移放大到目标城市，红点亮起，使用经典的优雅缓慢减速曲线
    homeGlobeTimeout = setTimeout(() => {
      mapEl.style.transition = "transform 2.2s cubic-bezier(0.16, 1, 0.3, 1)";
      mapEl.style.transform = `translate(${finalTx}px, ${finalTy}px) scale(${FINAL_ZOOM})`;
      pin.style.opacity = "1";
    }, 1800);
  }

  function getCountryCode(name) {
    const map = {
      "日本 · 京都": "jp",
      "冰岛 · 雷克雅未克": "is",
      "中国 · 四川竹海": "cn",
      "法国 · 巴黎": "fr",
      "摩洛哥 · 马拉喀什": "ma",
      "挪威 · 特罗姆瑟": "no",
      "瑞士 · 阿尔卑斯山小镇": "ch",
      "意大利 · 威尼斯": "it",
      "希腊 · 圣托里尼": "gr",
      "英国 · 伦敦": "gb",
      "加拿大 · 魁北克枫林": "ca",
      "埃及 · 开罗": "eg",
      "芬兰 · 罗瓦涅米": "fi",
      "新西兰 · 霍比屯": "nz",
      "中国 · 苏州园林": "cn"
    };
    return map[name] || null;
  }

  async function initWorldMap() {
    try {
      const response = await fetch("./assets/data/world-map.min.svg");
      if (!response.ok) throw new Error("地图文件加载失败");
      const svgText = await response.text();
      const container = document.getElementById("worldMapContainer");
      container.innerHTML = svgText;
      
      const svgElement = container.querySelector("svg");
      if (svgElement) {
        svgElement.setAttribute("width", "100%");
        svgElement.setAttribute("height", "100%");
        svgElement.setAttribute("preserveAspectRatio", "xMidYMid meet");
        
        let pinsGroup = svgElement.getElementById("mapPinsGroup");
        if (!pinsGroup) {
          pinsGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
          pinsGroup.setAttribute("id", "mapPinsGroup");
          svgElement.appendChild(pinsGroup);
        }
        
        renderMapPins();
      }
    } catch (e) {
      console.error("加载地图发生错误:", e);
      document.getElementById("worldMapContainer").innerHTML = `<div style="padding: 40px; text-align: center; color: var(--mist);">地图加载失败，请切换至印章手账视图。</div>`;
    }
  }

  function renderMapPins() {
    const svgElement = document.querySelector("#worldMapContainer svg");
    if (!svgElement) return;
    
    const pinsGroup = svgElement.getElementById("mapPinsGroup");
    if (!pinsGroup) return;
    
    pinsGroup.innerHTML = "";
    const history = getHistory();
    
    // 高亮去过的国家
    const visitedCountries = new Set();
    history.forEach(entry => {
      const loc = LOCATIONS.find(l => l.name === entry.location);
      const countryCode = loc ? loc.countryCode : getCountryCode(entry.location);
      if (countryCode) visitedCountries.add(countryCode.toLowerCase());
    });
    
    svgElement.querySelectorAll("path").forEach(path => {
      path.classList.remove("visited-country");
    });
    
    visitedCountries.forEach(code => {
      const path = svgElement.getElementById(code);
      if (path) {
        path.classList.add("visited-country");
      }
    });
    
    // 渲染所有城市的坐标点
    LOCATIONS.forEach((loc, index) => {
      let x, y;
      if (typeof loc.mapX === "number" && typeof loc.mapY === "number") {
        x = loc.mapX;
        y = loc.mapY;
      } else {
        const c = getCityViewBoxXY(loc) || { x: 2.220002 * loc.lng + 411.737295, y: -2.935935 * loc.lat + 533.594919 };
        x = c.x;
        y = c.y;
      }
      
      const visitedEntries = history.filter(entry => entry.location === loc.name);
      const isVisited = visitedEntries.length > 0;
      
      const pinG = document.createElementNS("http://www.w3.org/2000/svg", "g");
      pinG.setAttribute("class", `map-pin ${isVisited ? 'visited' : ''}`);
      pinG.setAttribute("data-name", loc.name);
      pinG.setAttribute("data-index", index);
      
      // 大洲分类属性 (用于检索过滤)
      let continent = "asia";
      const cc = (loc.countryCode || "").toLowerCase();
      if (["us", "ca", "mx", "br", "ar", "pe", "cl", "co"].includes(cc)) {
        continent = "americas";
      } else if (["fr", "no", "ch", "it", "gr", "gb", "fi", "is", "ru", "de", "at", "nl", "be", "dk", "se", "pl", "cz", "hu", "hr", "ro", "ie", "es", "pt"].includes(cc)) {
        continent = "europe";
      } else if (["eg", "ma", "za", "ke", "tz", "tn", "dz", "mg"].includes(cc)) {
        continent = "africa";
      } else if (["au", "nz", "fj"].includes(cc)) {
        continent = "oceania";
      }
      pinG.setAttribute("data-continent", continent);
      
      if (isVisited) {
        pinG.style.setProperty('--stamp-color', loc.stampColor);
      }
      
      // 呼吸外圈
      const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      glow.setAttribute("class", "pin-glow");
      glow.setAttribute("cx", x);
      glow.setAttribute("cy", y);
      glow.setAttribute("r", isVisited ? "12" : "5");
      pinG.appendChild(glow);
      
      // 实心内圈
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("class", "pin-dot");
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", y);
      dot.setAttribute("r", "4.5");
      pinG.appendChild(dot);
      
      // 悬停气泡提示逻辑
      pinG.addEventListener("mouseenter", (e) => {
        const tooltip = document.getElementById("mapTooltip");
        if (tooltip) {
          let text = `<strong>${loc.name}</strong>`;
          if (isVisited) {
            text += `<br/><span style="font-size: 10px; opacity: 0.95;">已探访 ${visitedEntries.length} 次<br/>上次于: ${visitedEntries[0].date}</span>`;
          } else {
            text += `<br/><span style="font-size: 10px; opacity: 0.65;">点击快捷切换并推窗开启探索</span>`;
          }
          tooltip.innerHTML = text;
          tooltip.style.opacity = "1";
        }
      });
      
      pinG.addEventListener("mousemove", (e) => {
        const tooltip = document.getElementById("mapTooltip");
        const container = document.getElementById("worldMapContainer");
        if (tooltip && container) {
          const rect = container.getBoundingClientRect();
          const tooltipWidth = tooltip.offsetWidth;
          const tooltipHeight = tooltip.offsetHeight;
          
          let left = e.clientX - rect.left + 10;
          let top = e.clientY - rect.top - tooltipHeight - 10;
          
          if (left + tooltipWidth > rect.width) {
            left = e.clientX - rect.left - tooltipWidth - 10;
          }
          if (top < 0) {
            top = e.clientY - rect.top + 15;
          }
          
          tooltip.style.left = left + "px";
          tooltip.style.top = top + "px";
        }
      });
      
      pinG.addEventListener("mouseleave", () => {
        const tooltip = document.getElementById("mapTooltip");
        if (tooltip) tooltip.style.opacity = "0";
      });
      
      pinG.addEventListener("click", () => {
        if (isVisited) {
          reviewPastTrip(visitedEntries[0].id);
        } else {
          // 快捷切换主界面的城市，并关闭抽屉
          currentLocationIndex = index;
          applyLocationSettings(currentLocationIndex);
          try {
            localStorage.setItem("breathe:currentLocationIndex", currentLocationIndex);
          } catch (e) {}
          toggleDrawer(false);
        }
      });
      
      pinsGroup.appendChild(pinG);
    });
  }

  // --- 地图检索与大洲过滤逻辑 ---
  let activeMapSearchQuery = "";
  let activeMapContinent = "all";

  function handleMapSearch() {
    const input = document.getElementById("mapSearchInput");
    if (!input) return;
    activeMapSearchQuery = input.value.trim().toLowerCase();
    applyMapFilters();
  }

  function filterContinent(continent, btn) {
    const buttons = document.querySelectorAll(".continent-filters .filter-btn");
    buttons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    
    activeMapContinent = continent;
    applyMapFilters();
  }

  function applyMapFilters() {
    const pins = document.querySelectorAll("#mapPinsGroup .map-pin");
    pins.forEach(pin => {
      const name = (pin.getAttribute("data-name") || "").toLowerCase();
      const continent = pin.getAttribute("data-continent") || "";
      
      const matchesSearch = activeMapSearchQuery === "" || name.includes(activeMapSearchQuery);
      
      let matchesContinent = false;
      if (activeMapContinent === "all") {
        matchesContinent = true;
      } else if (activeMapContinent === "africa_oceania") {
        matchesContinent = (continent === "africa" || continent === "oceania");
      } else {
        matchesContinent = (continent === activeMapContinent);
      }
      
      if (matchesSearch && matchesContinent) {
        pin.classList.remove("dimmed");
      } else {
        pin.classList.add("dimmed");
      }
    });
  }

  function getHistory() {
    try {
      const h = localStorage.getItem("breathe:history");
      return h ? JSON.parse(h) : [];
    } catch (e) {
      return [];
    }
  }

  function saveHistory(entry) {
    const history = getHistory();
    history.unshift(entry); // Add newest first
    try {
      localStorage.setItem("breathe:history", JSON.stringify(history));
      updateImprintsCount();
    } catch(e) {}
  }

  function updateImprintsCount() {
    const history = getHistory();
    document.getElementById("imprintsCount").textContent = history.length;
  }

  function renderTravelLog() {
    const history = getHistory();
    const grid = document.getElementById("stampGrid");
    const empty = document.getElementById("stampEmpty");
    
    grid.innerHTML = "";
    
    if (history.length === 0) {
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");
    
    history.forEach((entry, idx) => {
      const loc = LOCATIONS.find(l => l.name === entry.location) || LOCATIONS[entry.locationIndex || 0];
      const card = document.createElement("div");
      card.className = "stamp-card";
      card.onclick = () => reviewPastTrip(entry.id);
      
      const stampRot = (Math.sin(idx) * 6).toFixed(1) + "deg"; // Consistent random-looking rotation
      
      card.innerHTML = `
        <div class="ink-stamp" style="--stamp-color: ${loc.stampColor}; --stamp-rotate: ${stampRot}">
          <span class="ink-stamp-emblem">${loc.emblem}</span>
          <span class="ink-stamp-name">${loc.name.split(' · ')[1] || loc.name}</span>
          <span class="ink-stamp-sub">${entry.date.substring(5)}</span>
        </div>
        <div class="stamp-date">${entry.date}</div>
        <div class="stamp-time">${entry.time}</div>
      `;
      grid.appendChild(card);
    });
  }

  function reviewPastTrip(id) {
    const history = getHistory();
    const entry = history.find(e => e.id === id);
    if (!entry) return;
    
    isReviewMode = true;
    selectedReviewLocation = entry.location;
    selectedReviewDate = entry.date + " " + entry.time;
    
    toggleDrawer(false);
    
    // Transition from gate to feed
    document.getElementById("gate").classList.add("hidden");
    
    renderCards(entry.items);
    
    const feed = document.getElementById("feed");
    feed.classList.remove("hidden");
    feed.style.opacity = 1;
    feed.style.transform = "translateY(0)";
  }

  function exitReviewMode() {
    isReviewMode = false;
    
    const feed = document.getElementById("feed");
    feed.style.opacity = 0;
    feed.style.transform = "translateY(15px)";
    
    setTimeout(() => {
      feed.classList.add("hidden");
      
      const gate = document.getElementById("gate");
      gate.classList.remove("hidden");
      gate.style.opacity = 1;
      gate.style.transform = "translateY(0)";
      
      toggleDrawer(true);
    }, 400);
  }

  function confirmClearHistory() {
    if (confirm("确定要清空您的所有旅行历史印迹吗？清空后收集进度将被重置，无法恢复。")) {
      try {
        localStorage.removeItem("breathe:history");
        localStorage.removeItem(KEY_IS_OPEN);
        localStorage.removeItem(KEY_ITEMS);
        localStorage.removeItem(KEY_SLIDE_INDEX);
      } catch (e) {}
      
      updateImprintsCount();
      applyLocationSettings(currentLocationIndex, true);
      
      if (activeDrawerTab === "map") {
        renderMapPins();
      } else {
        renderTravelLog();
      }
    }
  }

  // --- 单页滑动呈现逻辑 ---
  let globalItems = [];
  let currentSlideIndex = 0;
  
  let loadedImages = {};
  let waitingForSlideIndex = null;

  function fixUrl(url) {
    if (!url) return url;
    if (url.startsWith('/')) return '.' + url;
    return url;
  }

  function getFallbackImage(bucket) {
    if (bucket === "世界一角") return "./assets/images/world_corner.png";
    if (bucket === "科学自然") return "./assets/images/science_nature.png";
    if (bucket === "他人在场") return "./assets/images/others_present.png";
    if (bucket === "思想火花") return "./assets/images/spark_of_thought.png";
    if (bucket === "旧物新看") return "./assets/images/old_knowledge.png";
    return "./assets/images/world_corner.png";
  }

  function preloadAllImages(items) {
    loadedImages = {};
    items.forEach((it, index) => {
      const imageUrl = fixUrl(it.image) || getFallbackImage(it.bucket);
      
      const img = new Image();
      img.src = imageUrl;
      img.onload = () => {
        loadedImages[index] = true;
        if (waitingForSlideIndex === index) {
          waitingForSlideIndex = null;
          performSlideTransition(index);
        }
      };
      img.onerror = () => {
        loadedImages[index] = true;
        if (waitingForSlideIndex === index) {
          waitingForSlideIndex = null;
          performSlideTransition(index);
        }
      };
    });
  }

  function renderCards(items) {
    globalItems = items;
    preloadAllImages(items);

    try {
      const savedIndex = localStorage.getItem(KEY_SLIDE_INDEX);
      if (savedIndex !== null && !isReviewMode) {
        currentSlideIndex = parseInt(savedIndex) || 0;
      } else {
        currentSlideIndex = 0;
      }
    } catch (e) {
      currentSlideIndex = 0;
    }
    
    if (loadedImages[currentSlideIndex]) {
      showSlide(currentSlideIndex);
    } else {
      waitingForSlideIndex = currentSlideIndex;
      renderSkeleton();
    }
  }

  function showSlide(index) {
    const wrap = document.getElementById("cards");
    wrap.innerHTML = "";

    const it = globalItems[index];
    if (!it) return;

    const card = document.createElement("div");
    card.className = "slide";

    const imageUrl = fixUrl(it.image) || getFallbackImage(it.bucket);
    const ponder = it.ponder ? `<div class="ponder">${escapeHtml(it.ponder)}</div>` : "";

    const prevBtn = index > 0 
      ? `<button class="nav-btn" onclick="changeSlide(${index - 1})">上一扇</button>`
      : `<button class="nav-btn" disabled>上一扇</button>`;

    const nextBtn = index < 4
      ? `<button class="nav-btn primary" onclick="changeSlide(${index + 1})">下一扇</button>`
      : (isReviewMode 
          ? `<button class="nav-btn primary" onclick="exitReviewMode()">返回手账</button>`
          : `<button class="nav-btn primary" onclick="closeWindowInteractive()">关 上 窗</button>`);

    let dotsHtml = '<div class="nav-dots">';
    for (let i = 0; i < 5; i++) {
      dotsHtml += `<span class="dot ${i === index ? 'active' : ''}"></span>`;
    }
    dotsHtml += '</div>';

    // Update lede label
    const lede = document.getElementById("feedLede");
    if (isReviewMode) {
      lede.innerHTML = `📍 ${selectedReviewLocation} · 旅行回顾 (${selectedReviewDate})`;
    } else {
      lede.textContent = "今天值得看一眼的五件事";
    }

    card.innerHTML = `
      <div class="image-box">
        <div class="image-paper-overlay"></div>
        <img src="${imageUrl}" class="slide-image" alt="${escapeHtml(it.bucket)}" onerror="this.onerror=null; this.src=getFallbackImage('${escapeHtml(it.bucket)}');">
      </div>
      <div class="slide-content">
        <span class="bucket">${escapeHtml(it.bucket || "")}</span>
        <div class="card-title">${escapeHtml(it.title || "")}</div>
        <div class="card-body">${escapeHtml(it.body || "")}</div>
        ${ponder}
      </div>
      <div class="slide-nav-wrapper">
        <div class="slide-nav">
          ${prevBtn}
          <div class="nav-indicator">
            ${dotsHtml}
          </div>
          ${nextBtn}
        </div>
      </div>
    `;
    wrap.appendChild(card);
  }

  function renderSkeleton() {
    const wrap = document.getElementById("cards");
    wrap.innerHTML = `
      <div class="slide skeleton">
        <div class="image-box skeleton-block skeleton-image" style="display:flex; align-items:center; justify-content:center;">
          <div class="loading-container" style="background:transparent; position:relative;">
            <div class="lightbar"></div>
          </div>
        </div>
        <div class="slide-content">
          <div class="skeleton-block skeleton-tag"></div>
          <div class="skeleton-block skeleton-title"></div>
          <div class="skeleton-block skeleton-body-line"></div>
          <div class="skeleton-block skeleton-body-line short"></div>
        </div>
        <div class="slide-nav-wrapper" style="opacity: 0.15; pointer-events: none;">
          <div class="slide-nav">
            <button class="nav-btn" disabled>上一扇</button>
            <div class="nav-indicator">推窗中...</div>
            <button class="nav-btn" disabled>下一扇</button>
          </div>
        </div>
      </div>
    `;
  }

  function changeSlide(index) {
    if (index === currentSlideIndex) return;
    const wrap = document.getElementById("cards");

    // 第一步：漂移淡出 (向上稍微飘移)
    wrap.style.opacity = 0;
    wrap.style.transform = "translateY(-10px)";

    setTimeout(() => {
      currentSlideIndex = index;
      if (!isReviewMode) {
        try {
          localStorage.setItem(KEY_SLIDE_INDEX, index);
        } catch(e) {}
      }

      if (loadedImages[index]) {
        // 已有缓存：临时禁用过渡，定位于下方，强制重绘，然后缓动升起
        wrap.style.transition = "none";
        showSlide(index);
        wrap.style.transform = "translateY(12px)";
        wrap.style.opacity = 0;
        wrap.offsetHeight; // 强制重绘
        
        wrap.style.transition = "opacity 1.2s cubic-bezier(0.25, 0.8, 0.25, 1), transform 1.2s cubic-bezier(0.25, 0.8, 0.25, 1)";
        wrap.style.opacity = 1;
        wrap.style.transform = "translateY(0)";
      } else {
        // 未加载完：展示骨架屏，等待图片载入完成后由 performSlideTransition 缓动推入
        waitingForSlideIndex = index;
        wrap.style.transition = "none";
        renderSkeleton();
        wrap.style.transform = "translateY(12px)";
        wrap.style.opacity = 0;
        wrap.offsetHeight; // 强制重绘
        
        wrap.style.transition = "opacity 1.2s cubic-bezier(0.25, 0.8, 0.25, 1), transform 1.2s cubic-bezier(0.25, 0.8, 0.25, 1)";
        wrap.style.opacity = 1;
        wrap.style.transform = "translateY(0)";
      }
    }, 1100); 
  }

  function performSlideTransition(index) {
    const wrap = document.getElementById("cards");
    
    // 从骨架屏过渡到卡片内容：先向上微调淡出，再换卡片升起
    wrap.style.opacity = 0;
    wrap.style.transform = "translateY(-8px)";
    
    setTimeout(() => {
      showSlide(index);
      wrap.style.transition = "none";
      wrap.style.transform = "translateY(12px)";
      wrap.style.opacity = 0;
      wrap.offsetHeight; // 强制重绘
      
      wrap.style.transition = "opacity 1.2s cubic-bezier(0.25, 0.8, 0.25, 1), transform 1.2s cubic-bezier(0.25, 0.8, 0.25, 1)";
      wrap.style.opacity = 1;
      wrap.style.transform = "translateY(0)";
    }, 1000);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => (
      {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]
    ));
  }

  // --- API Call ---
  let apiPromise = null;
  let apiData = null;
  let apiError = null;

  async function fetchDailyContent() {
    const today = todayLabel();
    const loc = LOCATIONS[currentLocationIndex] ? LOCATIONS[currentLocationIndex].name : null;
    
    // 优先尝试本地后端 API (server.py)
    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dateLabel: today, location: loc })
      });
      if (response.ok) {
        const data = await response.json();
        if (data.items && data.items.length > 0) {
          return data.items;
        }
      }
    } catch (e) {
      console.log("后端 API 未就绪或运行在 GitHub Pages 静态环境，切换至本地画册 catalog.json", e);
    }

    // 静态托管环境 (GitHub Pages) 降级读取 catalog.json
    const res = await fetch("./assets/data/catalog.json");
    if (!res.ok) throw new Error("加载画册数据库失败 (" + res.status + ")");
    const catalogData = await res.json();
    
    if (loc && catalogData[loc]) {
      return catalogData[loc];
    } else if (Object.keys(catalogData).length > 0) {
      const firstKey = Object.keys(catalogData)[0];
      return catalogData[firstKey];
    }
    
    throw new Error("未找到对应地点的插画画册");
  }

  // --- 地理特色加载词 ---
  function getLoadingWords(locationName) {
    const defaultWords = [
      "正在收拾精神行李…",
      "正在校准时空坐标…",
      "推开通往远方的门…",
      "正在挑些你白天碰不到的景色…"
    ];
    const locMap = {
      "日本 · 京都": [
        "正在换乘前往京都的列车…",
        "鸭川的晚风吹拂而来…",
        "清水寺的钟声隐约在耳…",
        "格子窗外，樱花瓣正在飞舞…"
      ],
      "冰岛 · 雷克雅未克": [
        "正在跨越冰岛的苔原…",
        "午夜的霞光已经升起…",
        "远处海湾正泛着碎冰的光芒…",
        "站在雷克雅未克街角看雪…"
      ],
      "中国 · 四川竹海": [
        "正在步入翠绿的竹林深处…",
        "竹叶上的晨露正悄然滴落…",
        "听见山间清新的风声…",
        "万亩毛竹如绿海起伏…"
      ],
      "法国 · 巴黎": [
        "正在塞纳河畔漫步…",
        "绿色的旧书摊已逐个推开…",
        "日落余晖洒在金色的波光上…",
        "街角的咖啡馆正传来乐曲…"
      ],
      "摩洛哥 · 马拉喀什": [
        "正在穿过老城的红土小巷…",
        "阳光穿透竹编顶棚斑驳落下…",
        "香料市集散发着清甜香气…",
        "晚霞染红了古老的宣礼塔…"
      ],
      "挪威 · 特罗姆瑟": [
        "正在飞往特罗姆瑟的夜空…",
        "幽绿的极光已悄然起舞…",
        "雪地木屋里的炉火正旺…",
        "看白雪覆盖安静的峡湾…"
      ],
      "瑞士 · 阿尔卑斯山小镇": [
        "正在整理前往阿尔卑斯山小镇的装备…",
        "听见远方雪峰下清脆的牛铃声…",
        "木屋窗外，积雪正反射着松针的淡绿…",
        "清冽的山风吹过落叶松林…"
      ],
      "意大利 · 威尼斯": [
        "正在踏上通往威尼斯的水上拱桥…",
        "贡多拉的桨声在静谧水道间回荡…",
        "红木横格窗外，水波折射出叹息桥的倒影…",
        "微风带起亚得里亚海略带咸味的气息…"
      ],
      "希腊 · 圣托里尼": [
        "正在爬上圣托里尼的白色台阶…",
        "爱琴海的湛蓝正在眼前徐游铺开…",
        "蓝色圆顶衬着一抹淡橘色的晚霞…",
        "微风轻抚着白墙上怒放的三角梅…"
      ],
      "英国 · 伦敦": [
        "正在穿过泰晤士河上的迷雾…",
        "听见大本钟沉稳悠扬的钟鸣…",
        "双悬木格窗外，红色双层巴士正缓缓驶过…",
        "泰晤士河上升起一缕温暖的灯光…"
      ],
      "加拿大 · 魁北克枫林": [
        "正在漫步在魁北克的金黄枫林中…",
        "踩在松软的枫叶地毯上发出沙沙脆响…",
        "橡木方格窗外，一片枫红如火飘落…",
        "壁炉里红枫木正散发着淡淡的甜香…"
      ],
      "埃及 · 开罗": [
        "正在穿越开罗的焦铜色黄沙…",
        "古老金字塔在夕阳下拉出长长的投影…",
        "几何铜格窗外，驼铃声渐行渐远…",
        "尼罗河畔正吹起滚烫而温和的晚风…"
      ],
      "芬兰 · 罗瓦涅米": [
        "正在踏入罗瓦涅米的银白雪原…",
        "圣诞老人的驯鹿正踏雪穿行林间…",
        "红色小方窗内，炉火正映红松木矮椅…",
        "夜空中正酝酿着一片纯净的雪花…"
      ],
      "新西兰 · 霍比屯": [
        "正在探寻霍比屯的绿色山丘…",
        "圆木门旁，雏菊正迎着晨光摇曳…",
        "阳光洒在矮桥与静谧的小溪上…",
        "空气里弥漫着泥土与青草的清香…"
      ],
      "中国 · 苏州园林": [
        "正在踏上粉墙黛瓦下的青石小径…",
        "冰裂纹漏窗外，一枝翠竹正临风摇曳…",
        "听见留园太湖石旁游鱼戏水的声音…",
        "雨丝飘落在芭蕉叶上，泛起阵阵涟漪…"
      ]
    };
    return locMap[locationName] || [
      `正在收拾前往 ${locationName} 的精神行李…`,
      `正在校准 ${locationName} 的时空坐标…`,
      `推开通往 ${locationName} 的那扇窗户…`,
      `正在挑选 ${locationName} 此时此刻的景色…`
    ];
  }

  function startDecompression() {
    document.getElementById("btnGroup").classList.add("fade-out");
    document.getElementById("locBadgeWrapper").classList.add("fade-out");
    const globeWrapper = document.getElementById("homeGlobeWrapper");
    if (globeWrapper) globeWrapper.classList.add("hidden");
    
    // 立即展示加载遮罩
    document.getElementById("loadingOverlay").classList.remove("hidden");
    cycleLoadingWords();
    
    isGenerating = true;
    apiData = null;
    apiError = null;
    
    // 引入6.0秒的人为延迟，让用户有足够时间阅读 3 句精美的载入词，并缓冲心情
    const fetchPromise = fetchDailyContent();
    const delayPromise = new Promise(resolve => setTimeout(resolve, 6000));
    
    Promise.all([fetchPromise, delayPromise])
      .then(([items]) => {
        isGenerating = false;
        stopLoadingWords();
        document.getElementById("loadingOverlay").classList.add("hidden");
        executeWindowOpen(items);
      })
      .catch(err => {
        isGenerating = false;
        stopLoadingWords();
        document.getElementById("loadingOverlay").classList.add("hidden");
        showFailState(err);
      });
  }

  function executeWindowOpen(items) {
    // 触发木窗打开的拟物音效
    AudioEngine.playWindowOpen();

    document.getElementById("shutterLeft").classList.add("open");
    document.getElementById("shutterRight").classList.add("open");
    document.getElementById("windowLight").classList.add("glowing");

    try {
      localStorage.setItem(KEY_IS_OPEN, "true");
      localStorage.setItem(KEY_ITEMS, JSON.stringify(items));
      localStorage.setItem(KEY_SLIDE_INDEX, "0"); 
    } catch (e) {}

    preloadAllImages(items);

    setTimeout(() => {
      const wrapper = document.getElementById("windowWrapper");
      wrapper.classList.add("zoomed");
      
      document.getElementById("gateTitle").classList.add("fade-out");
      document.getElementById("gateSub").classList.add("fade-out");
      
      setTimeout(() => {
        const gate = document.getElementById("gate");
        gate.classList.add("hidden");
        
        wrapper.classList.remove("zoomed");
        document.getElementById("shutterLeft").classList.remove("open");
        document.getElementById("shutterRight").classList.remove("open");
        document.getElementById("windowLight").classList.remove("glowing");
        document.getElementById("gateTitle").classList.remove("fade-out");
        document.getElementById("gateSub").classList.remove("fade-out");
        document.getElementById("btnGroup").classList.remove("fade-out");
        document.getElementById("locBadgeWrapper").classList.remove("fade-out");

        renderCards(items);
        
        const feed = document.getElementById("feed");
        feed.classList.remove("hidden");
        feed.style.opacity = 0;
        feed.style.transform = "translateY(15px)";
        
        setTimeout(() => {
          feed.style.opacity = 1;
          feed.style.transform = "translateY(0)";
        }, 50);
      }, 1200);

    }, 800); 
  }

  // --- Stamping Ceremony & Close Window ---
  function closeWindowInteractive() {
    if (isReviewMode) {
      exitReviewMode();
      return;
    }
    
    // Trigger stamping ceremony
    const overlay = document.getElementById("stampOverlayScreen");
    const stamp = document.getElementById("ceremonyStamp");
    const woodStamp = document.getElementById("woodenStamp");
    const pWrapper = document.getElementById("postcardWrapper");
    
    const loc = LOCATIONS[currentLocationIndex];
    const today = new Date();
    const timeStr = formatTime(today);
    const dateStrShort = todayLabelShort();
    
    const history = getHistory();
    const serialNum = history.length + 1;
    const serialStr = "第 " + String(serialNum).padStart(3, '0') + " 次开窗";
    
    // Save to localStorage history
    const entry = {
      id: "trip_" + Date.now(),
      date: dateStrShort,
      time: timeStr,
      location: loc.name,
      locationIndex: currentLocationIndex,
      items: globalItems
    };
    saveHistory(entry);
    
    // Set stamp design properties
    stamp.style.setProperty('--stamp-color', loc.stampColor);
    const rotDeg = (Math.random() * 8 - 4).toFixed(1) + "deg";
    stamp.style.setProperty('--stamp-rotate', rotDeg);
    
    document.getElementById("ceremonyStampEmblem").textContent = loc.emblem;
    document.getElementById("ceremonyStampName").textContent = loc.name.split(' · ')[1];
    document.getElementById("ceremonyStampDate").textContent = (today.getMonth() + 1) + "." + today.getDate();
    
    document.getElementById("postcardTag").textContent = "📍 " + loc.name;
    document.getElementById("postcardTime").textContent = todayLabel();
    document.getElementById("postcardSerial").textContent = serialStr;
    
    // Clean up classes
    stamp.classList.remove("stamped");
    overlay.classList.remove("hidden");
    
    // Fade overlay in (peacefully show postcard)
    setTimeout(() => {
      overlay.classList.add("visible");
      
      // Stamp begins blooming (slow ink-bleeding fade-in after 500ms)
      setTimeout(() => {
        stamp.classList.add("stamped");
        
        // Keep showing the completed postcard, then fade out and return to gate
        setTimeout(() => {
          overlay.classList.remove("visible");
          setTimeout(() => {
            overlay.classList.add("hidden");
            performGateReset();
          }, 600); // overlay fade out transition duration
          
        }, 2500); // 1.8s transition + 700ms peaceful reading
        
      }, 500);
      
    }, 50);
  }

  function performGateReset() {
    window.scrollTo({ top: 0, behavior: 'smooth' });

    const feed = document.getElementById("feed");
    feed.style.opacity = 0;
    feed.style.transform = "translateY(15px)";

    // Update visited stamp seal status immediately
    applyLocationSettings(currentLocationIndex, true);
    const globeWrapper = document.getElementById("homeGlobeWrapper");
    if (globeWrapper) globeWrapper.classList.remove("hidden");

    setTimeout(() => {
      feed.classList.add("hidden");

      try {
        localStorage.removeItem(KEY_IS_OPEN);
        localStorage.removeItem(KEY_ITEMS);
        localStorage.removeItem(KEY_SLIDE_INDEX);
      } catch (e) {}

      const gate = document.getElementById("gate");
      const wrapper = document.getElementById("windowWrapper");
      
      document.getElementById("shutterLeft").classList.add("open");
      document.getElementById("shutterRight").classList.add("open");
      document.getElementById("windowLight").classList.add("glowing");
      
      document.getElementById("btnGroup").classList.add("fade-out");
      document.getElementById("locBadgeWrapper").classList.add("fade-out");
      document.getElementById("gateTitle").classList.add("fade-out");
      document.getElementById("gateSub").classList.add("fade-out");

      wrapper.classList.add("zoomed");
      
      const originalTransition = wrapper.style.transition;
      wrapper.style.transition = 'none';
      
      gate.classList.remove("hidden");
      gate.style.opacity = 1;
      gate.style.transform = "translateY(0)";
      
      wrapper.offsetHeight;
      wrapper.style.transition = originalTransition;
      
      wrapper.classList.remove("zoomed");
      document.getElementById("gateTitle").classList.remove("fade-out");
      document.getElementById("gateSub").classList.remove("fade-out");
      document.getElementById("locBadgeWrapper").classList.remove("fade-out");
      
      setTimeout(() => {
        document.getElementById("shutterLeft").classList.remove("open");
        document.getElementById("shutterRight").classList.remove("open");
        document.getElementById("windowLight").classList.remove("glowing");
        
        setTimeout(() => {
          document.getElementById("btnGroup").classList.remove("fade-out");
        }, 800);

      }, 1200);

    }, 200);
  }

  function showFailState(err) {
    document.getElementById("failReason").textContent = err.message || "未知错误";
    document.getElementById("btnGroup").classList.remove("fade-out");
    document.getElementById("locBadgeWrapper").classList.remove("fade-out");
    show("fail");
  }

  // --- 加载文字轮播模块 ---
  let loadingTimer = null;
  function cycleLoadingWords() {
    const loc = LOCATIONS[currentLocationIndex];
    const words = getLoadingWords(loc.name);
    let i = 0;
    const el = document.getElementById("loadingWord");
    el.textContent = words[0];
    loadingTimer = setInterval(() => {
      i = (i + 1) % words.length;
      el.style.opacity = 0;
      setTimeout(() => { el.textContent = words[i]; el.style.opacity = 1; }, 300);
    }, 2000);
  }
  function stopLoadingWords() {
    if (loadingTimer) { clearInterval(loadingTimer); loadingTimer = null; }
  }

  /* ——— 治愈系 BGM 混音音效引擎 (Web Audio API Engine) ——— */
  const AudioEngine = {
    ctx: null,
    bgmGain: null,
    bgmBuffer: null,
    bgmSource: null,
    sfxBuffer: null,
    isPlaying: false,
    isLoaded: false,

    init() {
      if (this.ctx) return;
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      this.ctx = new AudioCtx();
      this.bgmGain = this.ctx.createGain();
      this.bgmGain.gain.value = 0;
      this.bgmGain.connect(this.ctx.destination);
      
      this.loadBgm();
      this.loadSfx();
    },

    async loadBgm() {
      try {
        const resp = await fetch('./assets/audio/healing_bgm.wav');
        if (!resp.ok) throw new Error('Audio fetch error');
        const arrayBuf = await resp.arrayBuffer();
        this.bgmBuffer = await this.ctx.decodeAudioData(arrayBuf);
        this.isLoaded = true;
      } catch(e) {
        console.log("AudioEngine: BGM asset loaded or fallback ready.");
      }
    },

    async loadSfx() {
      try {
        const resp = await fetch('./assets/audio/window_open.wav');
        if (resp.ok) {
          const arrayBuf = await resp.arrayBuffer();
          this.sfxBuffer = await this.ctx.decodeAudioData(arrayBuf);
        }
      } catch(e) {}
    },

    toggle() {
      if (!this.ctx) this.init();
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      if (this.isPlaying) {
        this.disable();
      } else {
        this.enable();
      }
    },

    enable() {
      if (!this.ctx) this.init();
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
      
      if (this.bgmBuffer && !this.bgmSource) {
        this.bgmSource = this.ctx.createBufferSource();
        this.bgmSource.buffer = this.bgmBuffer;
        this.bgmSource.loop = true;
        this.bgmSource.connect(this.bgmGain);
        this.bgmSource.start(0);
      }
      
      // 平滑 1.5 秒渐入
      const now = this.ctx.currentTime;
      this.bgmGain.gain.cancelScheduledValues(now);
      this.bgmGain.gain.setValueAtTime(this.bgmGain.gain.value, now);
      this.bgmGain.gain.linearRampToValueAtTime(0.35, now + 1.5);
      
      this.isPlaying = true;
      try { localStorage.setItem('breathe_window_bgm', 'enabled'); } catch(e) {}
      this.updateUI();
    },

    disable() {
      if (!this.ctx) return;
      // 平滑 1.0 秒渐出
      const now = this.ctx.currentTime;
      this.bgmGain.gain.cancelScheduledValues(now);
      this.bgmGain.gain.setValueAtTime(this.bgmGain.gain.value, now);
      this.bgmGain.gain.linearRampToValueAtTime(0.0, now + 1.0);
      
      setTimeout(() => {
        if (!this.isPlaying && this.bgmSource) {
          try {
            this.bgmSource.stop();
            this.bgmSource.disconnect();
          } catch(e) {}
          this.bgmSource = null;
        }
      }, 1000);

      this.isPlaying = false;
      try { localStorage.setItem('breathe_window_bgm', 'disabled'); } catch(e) {}
      this.updateUI();
    },

    playWindowOpen() {
      if (!this.ctx) this.init();
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }

      if (this.sfxBuffer) {
        try {
          const sfx = this.ctx.createBufferSource();
          const gain = this.ctx.createGain();
          gain.gain.value = 0.5;
          sfx.buffer = this.sfxBuffer;
          sfx.connect(gain);
          gain.connect(this.ctx.destination);
          sfx.start(0);
          return;
        } catch(e) {}
      }
      this.synthCreak();
    },

    synthCreak() {
      if (!this.ctx) return;
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        const now = this.ctx.currentTime;
        osc.frequency.setValueAtTime(140, now);
        osc.frequency.exponentialRampToValueAtTime(240, now + 0.6);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.6);
      } catch(e) {}
    },

    updateUI() {
      const toggleBtn = document.getElementById('bgmToggle');
      const iconSpan = document.getElementById('bgmIcon');
      const eqSpan = document.getElementById('bgmEqualizer');
      if (!toggleBtn) return;

      if (this.isPlaying) {
        toggleBtn.classList.add('playing');
        if (iconSpan) iconSpan.innerText = '🎶';
        if (eqSpan) eqSpan.classList.remove('hidden');
      } else {
        toggleBtn.classList.remove('playing');
        if (iconSpan) iconSpan.innerText = '🎵';
        if (eqSpan) eqSpan.classList.add('hidden');
      }
    }
  };

  function toggleBGM() {
    AudioEngine.toggle();
  }

  async function boot() {
    document.getElementById("date").textContent = todayLabel();
    document.getElementById("loadingWord").style.transition = "opacity 0.3s ease";

    try {
      if (localStorage.getItem('breathe_window_bgm') === 'enabled') {
        const unlock = () => {
          AudioEngine.enable();
          window.removeEventListener('click', unlock);
          window.removeEventListener('touchstart', unlock);
        };
        window.addEventListener('click', unlock, { once: true });
        window.addEventListener('touchstart', unlock, { once: true });
      }
    } catch(e) {}

    // 动态加载所有选址元数据 locations.json
    try {
      const response = await fetch("./assets/data/locations.json");
      if (response.ok) {
        const rawData = await response.json();
        
        // 备份并恢复上次保存的城市名称以防止过滤后索引错位
        let savedCityName = null;
        try {
          const savedLoc = localStorage.getItem("breathe:currentLocationIndex");
          if (savedLoc !== null) {
            const savedIdx = parseInt(savedLoc) || 0;
            if (savedIdx >= 0 && savedIdx < rawData.length) {
              savedCityName = rawData[savedIdx].name;
            }
          }
        } catch(e) {}
        
        // 只保留具有全部专属插画的城市
        const data = rawData.filter(loc => loc.hasCustomImages === true);
        
        // 排序（虽然都是 true，仍保留以防万一）
        data.sort((a, b) => {
          const aHas = a.hasCustomImages === true ? 1 : 0;
          const bHas = b.hasCustomImages === true ? 1 : 0;
          return bHas - aHas;
        });
        
        LOCATIONS.length = 0;
        LOCATIONS.push(...data);
        
        if (savedCityName) {
          const newIdx = LOCATIONS.findIndex(l => l.name === savedCityName);
          if (newIdx !== -1) {
            currentLocationIndex = newIdx;
          } else {
            currentLocationIndex = 0;
          }
        }
      } else {
        console.error("加载 locations.json 失败:", response.statusText);
      }
    } catch (e) {
      console.error("网络请求 locations.json 失败:", e);
    }
    
    // 确保当前索引合法
    if (currentLocationIndex >= LOCATIONS.length) {
      currentLocationIndex = 0;
    }
    
    if (LOCATIONS.length > 0) {
      await initHomeGlobe();
      applyLocationSettings(currentLocationIndex, true);
    }
    updateImprintsCount();

    try {
      const isOpen = localStorage.getItem(KEY_IS_OPEN);
      if (isOpen === "true") {
        const savedItems = localStorage.getItem(KEY_ITEMS);
        if (savedItems) {
          const items = JSON.parse(savedItems);
          
          const hasFallbackImage = items.some(item => 
            item.image && (
              item.image.includes("world_corner.png") ||
              item.image.includes("science_nature.png") ||
              item.image.includes("others_present.png") ||
              item.image.includes("spark_of_thought.png") ||
              item.image.includes("old_knowledge.png")
            )
          );
          const loc = LOCATIONS[currentLocationIndex];
          const isOutdatedCache = loc && loc.hasCustomImages && hasFallbackImage;

          const isOldFormat = !Array.isArray(items) || 
                              items.some(item => !item.image || item.image.startsWith('http') || item.image.includes('picsum')) ||
                              isOutdatedCache;
          if (isOldFormat) {
            localStorage.removeItem(KEY_IS_OPEN);
            localStorage.removeItem(KEY_ITEMS);
            localStorage.removeItem(KEY_SLIDE_INDEX);
            try {
              localStorage.removeItem("breathe:demo");
            } catch (e) {}
          } else {
            document.getElementById("btnGroup").classList.add("fade-out");
            document.getElementById("locBadgeWrapper").classList.add("fade-out");
            document.getElementById("gate").classList.add("hidden");
            const globeWrapper = document.getElementById("homeGlobeWrapper");
            if (globeWrapper) globeWrapper.classList.add("hidden");

            renderCards(items);
            
            const feed = document.getElementById("feed");
            feed.classList.remove("hidden");
            feed.style.opacity = 1;
            feed.style.transform = "translateY(0)";
            return;
          }
        }
      }
    } catch (e) { /* 读取失败 */ }

    show("gate");
  }

  boot();
