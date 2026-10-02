const API_BASE_URL = "http://localhost:8000/api/v1";

// 1. Initializing the MapLibre map with a free OpenStreetMap basemap
const map = new maplibregl.Map({
  container: "map",
  style: "https://tiles.openfreemap.org/styles/liberty", // Royalty-free vector background (no key required)
  center: [3.523, 50.358], // Centered on Valenciennes, [lon, lat]
  zoom: 13
});

// Adding zoom and compass controls
map.addControl(new maplibregl.NavigationControl(), "top-right");

// DOM elements
const sportFilter = document.getElementById("sport-filter");
const locateBtn = document.getElementById("locate-btn");
const spotsCount = document.getElementById("spots-count");

// Function to retrieve data according to the visible extent (bbox)
async function loadFacilitiesBBox() {
  const bounds = map.getBounds();
  const minLon = bounds.getWest();
  const minLat = bounds.getSouth();
  const maxLon = bounds.getEast();
  const maxLat = bounds.getNorth();
  const selectedSport = sportFilter.value;

  let url = `${API_BASE_URL}/facilities/bbox?min_lon=${minLon}&min_lat=${minLat}&max_lon=${maxLon}&max_lat=${maxLat}`;
  if (selectedSport) {
    url += `&sport=${encodeURIComponent(selectedSport)}`;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Erreur de récupération des données");
    const data = await response.json();

    // Upate the GeoJSON source with the new data
    const source = map.getSource("facilities-source");
    if (source) {
      source.setData(data);
    }

    spotsCount.textContent = data.features.length;
  } catch (error) {
    console.error("Échec du chargement des équipements :", error);
  }
}

// Initial loading of the layers once the style is ready
map.on("load", () => {
  map.addSource("facilities-source", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] }
  });

  // Graphic representation of the sports facilities as colored circles based on the sport type
  map.addLayer({
    id: "facilities-circles",
    type: "circle",
    source: "facilities-source",
    paint: {
      "circle-radius": 7,
      "circle-color": [
        "match",
        ["get", "sport"],
        "basketball", "#f97316",
        "soccer", "#22c55e",
        "fitness", "#3b82f6",
        "running", "#eab308",
        "#8b5cf6" // Color by default (multi/other)
      ],
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff"
    }
  });

  // Load facilities whenever the map is moved or zoomed
  map.on("moveend", loadFacilitiesBBox);

  // Initial load of facilities within the current map bounds
  loadFacilitiesBBox();
});

// Popup display when clicking on a facility
map.on("click", "facilities-circles", (e) => {
  const coordinates = e.features[0].geometry.coordinates.slice();
  const props = e.features[0].properties;

  const content = `
    <div class="popup-title">${props.name || "Sport court"}</div>
    <div class="popup-meta">
      <strong>Sport :</strong> ${props.sport || "Not specified"}<br/>
      <strong>Revêtement :</strong> ${props.surface || "Not specified"}<br/>
      <strong>Éclairage :</strong> ${props.lit === "yes" ? "Yes" : "No or unknown"}
    </div>
  `;

  new maplibregl.Popup()
    .setLngLat(coordinates)
    .setHTML(content)
    .addTo(map);
});

// Interactive cursor change when hovering over a facility
map.on("mouseenter", "facilities-circles", () => {
  map.getCanvas().style.cursor = "pointer";
});
map.on("mouseleave", "facilities-circles", () => {
  map.getCanvas().style.cursor = "";
});

// Listener on the sport filter
sportFilter.addEventListener("change", loadFacilitiesBBox);

// Geolocalisation ("Around me" button)
locateBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }

  locateBtn.textContent = "Locating ...";

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { longitude, latitude } = position.coords;
      map.flyTo({ center: [longitude, latitude], zoom: 15 });
      locateBtn.textContent = "Around me";
    },
    (err) => {
      alert("Impossible to get location : " + err.message);
      locateBtn.textContent = "Around me";
    }
  );
});


// Sort the sport filter options alphabetically
const select = document.getElementById("sport-filter");
const options = Array.from(select.options);
options.sort((a, b) => a.text.localeCompare(b.text));
options.forEach(option => select.appendChild(option));