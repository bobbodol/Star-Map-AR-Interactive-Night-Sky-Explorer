# star_map.js
/**
 * 🌟 Star Map AR – Interactive Night Sky Explorer (Node.js Edition)
 * Features: ASCII sky map, constellation tracing, star search, favourites, simulation
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

// ─── Colors ──────────────────────────────────────────────────────────────────

const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    dim: '\x1b[2m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
    white: '\x1b[37m',
};

const c = (str, color) => `${color}${str}${colors.reset}`;

// ─── Star Database ──────────────────────────────────────────────────────────

const STARS = [
    ["Sirius", 6.75, -16.72, -1.46, "Canis Major"],
    ["Canopus", 6.40, -52.70, -0.72, "Carina"],
    ["Rigil Kentaurus", 14.65, -60.83, -0.27, "Centaurus"],
    ["Arcturus", 14.25, 19.18, -0.05, "Boötes"],
    ["Vega", 18.62, 38.78, 0.03, "Lyra"],
    ["Capella", 5.27, 46.00, 0.08, "Auriga"],
    ["Rigel", 5.20, -8.20, 0.12, "Orion"],
    ["Procyon", 7.65, 5.23, 0.34, "Canis Minor"],
    ["Achernar", 1.63, -57.24, 0.45, "Eridanus"],
    ["Betelgeuse", 5.92, 7.41, 0.42, "Orion"],
    ["Hadar", 14.08, -60.37, 0.61, "Centaurus"],
    ["Altair", 19.85, 8.87, 0.76, "Aquila"],
    ["Aldebaran", 4.62, 16.51, 0.85, "Taurus"],
    ["Antares", 16.47, -26.43, 0.96, "Scorpius"],
    ["Spica", 13.42, -11.16, 0.98, "Virgo"],
    ["Pollux", 7.75, 28.03, 1.14, "Gemini"],
    ["Fomalhaut", 22.95, -29.62, 1.16, "Piscis Austrinus"],
    ["Deneb", 20.70, 45.28, 1.25, "Cygnus"],
    ["Regulus", 10.15, 11.97, 1.35, "Leo"],
    ["Adhara", 6.93, -29.00, 1.50, "Canis Major"],
    ["Castor", 7.63, 31.87, 1.58, "Gemini"],
    ["Gacrux", 12.47, -57.11, 1.63, "Crux"],
    ["Shaula", 17.48, -37.06, 1.62, "Scorpius"],
    ["Mintaka", 5.53, -0.30, 2.23, "Orion"],
    ["Alnilam", 5.63, -1.20, 1.69, "Orion"],
    ["Alnitak", 5.68, -1.95, 1.74, "Orion"],
    ["Saiph", 5.63, -9.67, 2.06, "Orion"],
    ["Bellatrix", 5.42, 6.35, 1.64, "Orion"],
    ["Alcyone", 3.72, 24.10, 2.87, "Taurus"],
    ["Mirfak", 3.38, 49.86, 1.79, "Perseus"],
    ["Algol", 3.08, 40.95, 2.09, "Perseus"],
    ["Caph", 0.17, 59.15, 2.28, "Cassiopeia"],
    ["Schedar", 0.68, 56.54, 2.24, "Cassiopeia"],
    ["Polaris", 2.52, 89.26, 1.97, "Ursa Minor"],
    ["Alioth", 12.90, 55.96, 1.76, "Ursa Major"],
    ["Dubhe", 11.05, 61.75, 1.79, "Ursa Major"],
    ["Merak", 11.03, 56.38, 2.37, "Ursa Major"],
    ["Phecda", 11.90, 53.69, 2.44, "Ursa Major"],
    ["Megrez", 12.25, 57.03, 3.31, "Ursa Major"],
    ["Mizar", 13.40, 54.93, 2.23, "Ursa Major"],
    ["Alkaid", 13.78, 49.31, 1.85, "Ursa Major"],
    ["Thuban", 14.08, 64.37, 3.65, "Draco"],
    ["Elnath", 5.45, 28.60, 1.65, "Taurus"],
    ["Menkalinan", 6.60, 44.85, 1.90, "Auriga"],
    ["Navi", 1.88, 62.60, 2.15, "Cassiopeia"],
    ["Ruchbah", 1.42, 60.72, 2.68, "Cassiopeia"],
    ["Segin", 1.08, 60.57, 3.37, "Cassiopeia"],
    ["Nihal", 5.75, -20.75, 2.80, "Lepus"],
];

// ─── User Data ─────────────────────────────────────────────────────────────

class UserData {
    constructor() {
        this.dataDir = path.join(os.homedir(), '.star_map');
        this.dataFile = path.join(this.dataDir, 'user.json');
        if (!fs.existsSync(this.dataDir)) fs.mkdirSync(this.dataDir, { recursive: true });
        this.favourites = [];
        this.latitude = 40.7;
        this.longitude = -74.0;
        this.timezone = -5;
        this._load();
    }

    _load() {
        if (fs.existsSync(this.dataFile)) {
            try {
                const data = JSON.parse(fs.readFileSync(this.dataFile, 'utf8'));
                this.favourites = data.favourites || [];
                this.latitude = data.latitude || 40.7;
                this.longitude = data.longitude || -74.0;
                this.timezone = data.timezone || -5;
            } catch (_) {}
        }
    }

    save() {
        fs.writeFileSync(this.dataFile, JSON.stringify({
            favourites: this.favourites,
            latitude: this.latitude,
            longitude: this.longitude,
            timezone: this.timezone
        }, null, 2));
    }

    toggleFavourite(name) {
        const idx = this.favourites.indexOf(name);
        if (idx >= 0) this.favourites.splice(idx, 1);
        else this.favourites.push(name);
        this.save();
    }

    isFavourite(name) { return this.favourites.includes(name); }
}

// ─── Sky Map Engine ─────────────────────────────────────────────────────────

class SkyMap {
    constructor(lat = 40.7, lon = -74.0, tz = -5) {
        this.lat = lat * Math.PI / 180;
        this.lon = lon * Math.PI / 180;
        this.tz = tz;
        this.stars = STARS;
        this.now = new Date();
    }

    setTime(dt) { this.now = dt; }

    _julianDate(dt) {
        let year = dt.getFullYear();
        let month = dt.getMonth() + 1;
        let day = dt.getDate() + dt.getHours() / 24 + dt.getMinutes() / 1440 + dt.getSeconds() / 86400;
        if (month <= 2) { year--; month += 12; }
        const A = Math.floor(year / 100);
        const B = 2 - A + Math.floor(A / 4);
        return Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + B - 1524.5;
    }

    _localSiderealTime(dt) {
        const jd = this._julianDate(dt);
        let gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * (jd - 2451545.0) ** 2;
        gmst = gmst % 360;
        let lst = gmst + this.lon * 180 / Math.PI;
        lst = lst % 360;
        return lst / 15.0; // hours
    }

    _altaz(ra_hours, dec_deg, dt) {
        const lst = this._localSiderealTime(dt);
        const ha = (lst - ra_hours) * 15 * Math.PI / 180;
        const dec = dec_deg * Math.PI / 180;
        const lat = this.lat;
        const alt = Math.asin(Math.sin(dec) * Math.sin(lat) + Math.cos(dec) * Math.cos(lat) * Math.cos(ha));
        let az = Math.atan2(-Math.sin(ha), Math.tan(dec) * Math.cos(lat) - Math.cos(ha) * Math.sin(lat));
        az = (az * 180 / Math.PI + 360) % 360;
        return { alt: alt * 180 / Math.PI, az };
    }

    getVisibleStars(minAlt = -10) {
        const visible = [];
        for (const [name, ra, dec, mag, constel] of this.stars) {
            const { alt, az } = this._altaz(ra, dec, this.now);
            if (alt > minAlt) {
                visible.push({ name, ra, dec, mag, constel, alt, az });
            }
        }
        return visible;
    }

    renderMap(width = 50, height = 20, highlightConst = null) {
        const visible = this.getVisibleStars();
        const grid = Array(height).fill().map(() => Array(width).fill(' '));
        const altMin = -10;
        const altMax = 90;
        for (const star of visible) {
            const alt = star.alt;
            const az = star.az;
            if (alt < altMin) continue;
            const row = Math.floor((alt - altMin) / (altMax - altMin) * (height - 1));
            const col = Math.floor((az / 360) * width) % width;
            const mag = star.mag;
            let ch;
            if (mag < 0) ch = '●';
            else if (mag < 1) ch = '◉';
            else if (mag < 2) ch = '○';
            else if (mag < 3) ch = '·';
            else ch = '.';
            if (highlightConst && star.constel.toLowerCase() === highlightConst.toLowerCase()) {
                ch = c(ch, 'yellow');
            } else {
                ch = c(ch, 'white');
            }
            grid[row][col] = ch;
        }
        return grid.map(row => row.join('')).join('\n');
    }
}

// ─── Main App ──────────────────────────────────────────────────────────────

class StarApp {
    constructor() {
        this.rl = readline.createInterface({ input: process.stdin, output: process.stdout });
        this.user = new UserData();
        this.sky = new SkyMap(this.user.latitude, this.user.longitude, this.user.timezone);
        this.highlightConst = null;
    }

    _ask(prompt) { return new Promise(resolve => this.rl.question(prompt, resolve)); }

    async _askFloat(prompt, def) {
        const ans = await this._ask(prompt);
        const val = parseFloat(ans.trim());
        return isNaN(val) ? def : val;
    }

    async _askInt(prompt, def) {
        const ans = await this._ask(prompt);
        const val = parseInt(ans.trim());
        return isNaN(val) ? def : val;
    }

    async showMenu() {
        console.log('\n' + c('═'.repeat(50), colors.cyan));
        console.log(c('🌟 STAR MAP AR', colors.bright + colors.cyan));
        console.log(c('═'.repeat(50), colors.cyan));
        console.log(`  Latitude: ${this.user.latitude.toFixed(1)}°  Longitude: ${this.user.longitude.toFixed(1)}°`);
        console.log(`  Time: ${this.sky.now.toISOString().replace('T', ' ').slice(0,16)}`);
        console.log(`  Highlight: ${this.highlightConst || 'None'}`);
        console.log(c('═'.repeat(50), colors.cyan));
        console.log('  1. 🌌 Show Sky Map');
        console.log('  2. ⭐ Search Star');
        console.log('  3. 🗺️  Highlight Constellation');
        console.log('  4. 📍 Set Location');
        console.log('  5. 🕒 Set Time');
        console.log('  6. ❤️  Toggle Favourite');
        console.log('  7. 📊 Favourites');
        console.log('  0. 🚪 Exit');
        console.log(c('═'.repeat(50), colors.cyan));
    }

    showMap() {
        console.log('\n🌌 Sky Map');
        const map = this.sky.renderMap(undefined, undefined, this.highlightConst);
        console.log(map);
    }

    async searchStar() {
        const query = await this._ask('⭐ Enter star name or constellation: ');
        const results = this.sky.stars.filter(([name, , , , constel]) =>
            name.toLowerCase().includes(query.toLowerCase()) ||
            constel.toLowerCase().includes(query.toLowerCase())
        );
        if (!results.length) {
            console.log(c('No stars found.', colors.yellow));
            return;
        }
        console.log(`\n🔍 Results (${results.length})`);
        for (const [name, ra, dec, mag, constel] of results) {
            const fav = this.user.isFavourite(name) ? '⭐' : ' ';
            console.log(`  ${fav} ${name}  RA:${ra.toFixed(2)}h  Dec:${dec.toFixed(2)}°  Mag:${mag.toFixed(2)}  ${constel}`);
        }
    }

    async highlightConstellation() {
        const constel = await this._ask('🗺️  Constellation name (or "none" to clear): ');
        if (constel.toLowerCase() === 'none') {
            this.highlightConst = null;
            console.log(c('Highlight cleared.', colors.dim));
            return;
        }
        const exists = this.sky.stars.some(([,,, , c]) => c.toLowerCase() === constel.toLowerCase());
        if (!exists) {
            console.log(c('Constellation not found.', colors.red));
            return;
        }
        this.highlightConst = constel;
        console.log(c(`Highlighting ${constel}`, colors.green));
    }

    async setLocation() {
        const lat = await this._askFloat(`📍 Latitude (default ${this.user.latitude}): `, this.user.latitude);
        const lon = await this._askFloat(`📍 Longitude (default ${this.user.longitude}): `, this.user.longitude);
        const tz = await this._askInt(`🕒 Timezone offset (default ${this.user.timezone}): `, this.user.timezone);
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180 || tz < -12 || tz > 14) {
            console.log(c('Invalid values.', colors.red));
            return;
        }
        this.user.latitude = lat;
        this.user.longitude = lon;
        this.user.timezone = tz;
        this.user.save();
        this.sky = new SkyMap(lat, lon, tz);
        console.log(c('✅ Location updated.', colors.green));
    }

    async setTime() {
        const dtStr = await this._ask('🕒 Enter date/time (YYYY-MM-DD HH:MM) or leave empty for now: ');
        if (!dtStr) {
            this.sky.now = new Date();
            console.log(c('Time set to current.', colors.dim));
            return;
        }
        const dt = new Date(dtStr.replace(' ', 'T'));
        if (isNaN(dt)) {
            console.log(c('Invalid format.', colors.red));
            return;
        }
        this.sky.setTime(dt);
        console.log(c(`Time set to ${dt.toISOString().replace('T', ' ').slice(0,16)}`, colors.green));
    }

    async toggleFavourite() {
        const name = await this._ask('❤️  Enter star name: ');
        const found = this.sky.stars.find(([n]) => n.toLowerCase() === name.toLowerCase());
        if (!found) {
            console.log(c('Star not found.', colors.red));
            return;
        }
        this.user.toggleFavourite(found[0]);
        const state = this.user.isFavourite(found[0]) ? 'added to' : 'removed from';
        console.log(c(`✅ ${found[0]} ${state} favourites.`, colors.green));
    }

    showFavourites() {
        const favs = this.user.favourites.filter(f => this.sky.stars.some(([n]) => n === f));
        if (!favs.length) {
            console.log(c('No favourites.', colors.yellow));
            return;
        }
        console.log('\n⭐ FAVOURITES');
        for (const name of favs) {
            const constel = this.sky.stars.find(([n]) => n === name)?.[4] || '';
            console.log(`  ${name} (${constel})`);
        }
    }

    async run() {
        console.clear();
        console.log(c('\n🌟 Star Map AR – Interactive Night Sky Explorer', colors.bright + colors.cyan));
        console.log(c('Explore the cosmos from your terminal!', colors.dim));

        while (true) {
            await this.showMenu();
            const choice = await this._ask('Your choice: ');
            switch (choice.trim()) {
                case '1': this.showMap(); break;
                case '2': await this.searchStar(); break;
                case '3': await this.highlightConstellation(); break;
                case '4': await this.setLocation(); break;
                case '5': await this.setTime(); break;
                case '6': await this.toggleFavourite(); break;
                case '7': this.showFavourites(); break;
                case '0':
                    console.log(c('👋 Clear skies!', colors.cyan));
                    this.rl.close();
                    return;
                default: console.log(c('❌ Invalid choice.', colors.red));
            }
            if (choice !== '0') {
                console.log('\nPress Enter to continue...');
                await this._ask('');
            }
        }
    }
}

// ─── Main ────────────────────────────────────────────────────────────────────

const main = async () => {
    try {
        const app = new StarApp();
        await app.run();
    } catch (e) {
        console.error(c(`❌ Unexpected error: ${e.message}`, colors.red));
        process.exit(1);
    }
};

main();
