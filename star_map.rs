# star_map.rs
/**
 * 🌟 Star Map AR – Interactive Night Sky Explorer (Rust Edition)
 * Features: ASCII sky map, constellation tracing, star search, favourites, simulation
 * Dependencies: serde, serde_json, chrono, colored
 */

use chrono::{DateTime, Local, NaiveDate, NaiveDateTime, NaiveTime, Timelike, Datelike};
use colored::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io::{self, Write, BufRead};
use std::path::PathBuf;

// ─── Types ──────────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize, Clone)]
struct Star {
    name: String,
    ra: f64,    // hours
    dec: f64,   // degrees
    mag: f64,
    constel: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct UserData {
    favourites: Vec<String>,
    latitude: f64,
    longitude: f64,
    timezone: i32,
}

// ─── Colors ──────────────────────────────────────────────────────────────────

fn c(text: &str, color: &str) -> String {
    match color {
        "green" => text.green().to_string(),
        "red" => text.red().to_string(),
        "yellow" => text.yellow().to_string(),
        "cyan" => text.cyan().to_string(),
        "bright" => text.bright().to_string(),
        "dim" => text.dimmed().to_string(),
        "white" => text.white().to_string(),
        _ => text.to_string(),
    }
}

// ─── Star Database ──────────────────────────────────────────────────────────

const STARS: &[Star] = &[
    // (same list as Python)
];

// ─── User Data Manager ─────────────────────────────────────────────────────

struct UserDataManager {
    file_path: PathBuf,
    data: UserData,
}

impl UserDataManager {
    fn new() -> Self {
        let home = std::env::var("HOME").or_else(|_| std::env::var("USERPROFILE")).unwrap_or_else(|_| ".".to_string());
        let dir = PathBuf::from(home).join(".star_map");
        fs::create_dir_all(&dir).unwrap();
        let file_path = dir.join("user.json");
        let mut ud = UserDataManager {
            file_path,
            data: UserData { favourites: Vec::new(), latitude: 40.7, longitude: -74.0, timezone: -5 },
        };
        ud.load();
        ud
    }

    fn load(&mut self) {
        if let Ok(raw) = fs::read_to_string(&self.file_path) {
            if let Ok(data) = serde_json::from_str::<UserData>(&raw) {
                self.data = data;
                return;
            }
        }
        self.data = UserData { favourites: Vec::new(), latitude: 40.7, longitude: -74.0, timezone: -5 };
    }

    fn save(&self) {
        let raw = serde_json::to_string_pretty(&self.data).unwrap();
        let _ = fs::write(&self.file_path, raw);
    }

    fn toggle_favourite(&mut self, name: &str) {
        if let Some(pos) = self.data.favourites.iter().position(|s| s == name) {
            self.data.favourites.remove(pos);
        } else {
            self.data.favourites.push(name.to_string());
        }
        self.save();
    }

    fn is_favourite(&self, name: &str) -> bool {
        self.data.favourites.contains(&name.to_string())
    }
}

// ─── Sky Map Engine ─────────────────────────────────────────────────────────

struct SkyMap {
    lat_rad: f64,
    lon_rad: f64,
    timezone: i32,
    now: DateTime<Local>,
    stars: Vec<Star>,
}

impl SkyMap {
    fn new(lat: f64, lon: f64, tz: i32) -> Self {
        SkyMap {
            lat_rad: lat.to_radians(),
            lon_rad: lon.to_radians(),
            timezone: tz,
            now: Local::now(),
            stars: STARS.to_vec(),
        }
    }

    fn set_time(&mut self, dt: DateTime<Local>) { self.now = dt; }

    fn julian_date(&self, dt: DateTime<Local>) -> f64 {
        let year = dt.year();
        let month = dt.month();
        let day = dt.day() as f64 + dt.hour() as f64 / 24.0 + dt.minute() as f64 / 1440.0 + dt.second() as f64 / 86400.0;
        let (y, m) = if month <= 2 {
            (year - 1, month + 12)
        } else {
            (year, month)
        };
        let A = (y / 100) as i32;
        let B = 2 - A + A / 4;
        (365.25 * (y as f64 + 4716.0)).floor() + (30.6001 * (m as f64 + 1.0)).floor() + day + B as f64 - 1524.5
    }

    fn local_sidereal_time(&self, dt: DateTime<Local>) -> f64 {
        let jd = self.julian_date(dt);
        let gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * (jd - 2451545.0).powi(2);
        let gmst = gmst % 360.0;
        let lst = gmst + self.lon_rad.to_degrees();
        let lst = lst % 360.0;
        lst / 15.0
    }

    fn altaz(&self, ra_hours: f64, dec_deg: f64, dt: DateTime<Local>) -> (f64, f64) {
        let lst = self.local_sidereal_time(dt);
        let ha = (lst - ra_hours) * 15.0 * std::f64::consts::PI / 180.0;
        let dec = dec_deg.to_radians();
        let lat = self.lat_rad;
        let alt = (dec.sin() * lat.sin() + dec.cos() * lat.cos() * ha.cos()).asin();
        let az = (-ha.sin()).atan2(dec.tan() * lat.cos() - ha.cos() * lat.sin());
        let az = (az.to_degrees() % 360.0 + 360.0) % 360.0;
        (alt.to_degrees(), az)
    }

    fn get_visible_stars(&self, min_alt: f64) -> Vec<(String, f64, f64, f64, String, f64, f64)> {
        let mut visible = Vec::new();
        for star in &self.stars {
            let (alt, az) = self.altaz(star.ra, star.dec, self.now);
            if alt > min_alt {
                visible.push((star.name.clone(), star.ra, star.dec, star.mag, star.constel.clone(), alt, az));
            }
        }
        visible
    }

    fn render_map(&self, width: usize, height: usize, highlight_const: Option<&str>) -> String {
        let visible = self.get_visible_stars(-10.0);
        let mut grid = vec![vec![' '; width]; height];
        let alt_min = -10.0;
        let alt_max = 90.0;
        for (name, ra, dec, mag, constel, alt, az) in visible {
            if alt < alt_min { continue; }
            let row = ((alt - alt_min) / (alt_max - alt_min) * (height - 1) as f64) as usize;
            let col = ((az / 360.0) * width as f64) as usize % width;
            let ch = if mag < 0.0 { '●' } else if mag < 1.0 { '◉' } else if mag < 2.0 { '○' } else if mag < 3.0 { '·' } else { '.' };
            let ch_str = if let Some(hc) = highlight_const {
                if constel.to_lowercase() == hc.to_lowercase() {
                    c(&ch.to_string(), "yellow")
                } else {
                    c(&ch.to_string(), "white")
                }
            } else {
                c(&ch.to_string(), "white")
            };
            grid[row][col] = ch_str.chars().next().unwrap_or(' ');
        }
        grid.iter().map(|row| row.iter().collect::<String>()).collect::<Vec<String>>().join("\n")
    }
}

// ─── Main App ──────────────────────────────────────────────────────────────

struct StarApp {
    user: UserDataManager,
    sky: SkyMap,
    highlight_const: Option<String>,
}

impl StarApp {
    fn new() -> Self {
        let user = UserDataManager::new();
        let sky = SkyMap::new(user.data.latitude, user.data.longitude, user.data.timezone);
        StarApp { user, sky, highlight_const: None }
    }

    fn ask(&self, prompt: &str) -> String {
        print!("{}", prompt);
        io::stdout().flush().unwrap();
        let mut line = String::new();
        io::stdin().read_line(&mut line).unwrap();
        line.trim().to_string()
    }

    fn ask_float(&self, prompt: &str, def: f64) -> f64 {
        loop {
            let ans = self.ask(prompt);
            if ans.is_empty() { return def; }
            if let Ok(val) = ans.parse::<f64>() { return val; }
            println!("{}", c("Please enter a number.", "yellow"));
        }
    }

    fn ask_int(&self, prompt: &str, def: i32) -> i32 {
        loop {
            let ans = self.ask(prompt);
            if ans.is_empty() { return def; }
            if let Ok(val) = ans.parse::<i32>() { return val; }
            println!("{}", c("Please enter a number.", "yellow"));
        }
    }

    fn show_menu(&self) {
        println!("\n{}", "═".repeat(50).cyan());
        println!("{}", c("🌟 STAR MAP AR", "bright cyan"));
        println!("{}", "═".repeat(50).cyan());
        println!("  Latitude: {:.1}°  Longitude: {:.1}°", self.user.data.latitude, self.user.data.longitude);
        println!("  Time: {}", self.sky.now.format("%Y-%m-%d %H:%M"));
        println!("  Highlight: {}", self.highlight_const.as_deref().unwrap_or("None"));
        println!("{}", "═".repeat(50).cyan());
        println!("  1. 🌌 Show Sky Map");
        println!("  2. ⭐ Search Star");
        println!("  3. 🗺️  Highlight Constellation");
        println!("  4. 📍 Set Location");
        println!("  5. 🕒 Set Time");
        println!("  6. ❤️  Toggle Favourite");
        println!("  7. 📊 Favourites");
        println!("  0. 🚪 Exit");
        println!("{}", "═".repeat(50).cyan());
    }

    fn show_map(&self) {
        println!("\n🌌 Sky Map");
        let map = self.sky.render_map(50, 20, self.highlight_const.as_deref());
        println!("{}", map);
    }

    fn search_star(&self) {
        let query = self.ask("⭐ Enter star name or constellation: ");
        let results: Vec<&Star> = self.sky.stars.iter()
            .filter(|s| s.name.to_lowercase().contains(&query.to_lowercase()) ||
                         s.constel.to_lowercase().contains(&query.to_lowercase()))
            .collect();
        if results.is_empty() {
            println!("{}", c("No stars found.", "yellow"));
            return;
        }
        println!("\n🔍 Results ({})", results.len());
        for s in results {
            let fav = if self.user.is_favourite(&s.name) { "⭐" } else { " " };
            println!("  {} {}  RA:{:.2}h  Dec:{:.2}°  Mag:{:.2}  {}", fav, s.name, s.ra, s.dec, s.mag, s.constel);
        }
    }

    fn highlight_constellation(&mut self) {
        let constel = self.ask("🗺️  Constellation name (or 'none' to clear): ");
        if constel.to_lowercase() == "none" {
            self.highlight_const = None;
            println!("{}", c("Highlight cleared.", "dim"));
            return;
        }
        let exists = self.sky.stars.iter().any(|s| s.constel.to_lowercase() == constel.to_lowercase());
        if !exists {
            println!("{}", c("Constellation not found.", "red"));
            return;
        }
        self.highlight_const = Some(constel.clone());
        println!("{}", c(&format!("Highlighting {}", constel), "green"));
    }

    fn set_location(&mut self) {
        let lat = self.ask_float("📍 Latitude (default ".to_string() + &self.user.data.latitude.to_string() + "): ", self.user.data.latitude);
        let lon = self.ask_float("📍 Longitude (default ".to_string() + &self.user.data.longitude.to_string() + "): ", self.user.data.longitude);
        let tz = self.ask_int("🕒 Timezone offset (default ".to_string() + &self.user.data.timezone.to_string() + "): ", self.user.data.timezone);
        if lat < -90.0 || lat > 90.0 || lon < -180.0 || lon > 180.0 || tz < -12 || tz > 14 {
            println!("{}", c("Invalid values.", "red"));
            return;
        }
        self.user.data.latitude = lat;
        self.user.data.longitude = lon;
        self.user.data.timezone = tz;
        self.user.save();
        self.sky = SkyMap::new(lat, lon, tz);
        println!("{}", c("✅ Location updated.", "green"));
    }

    fn set_time(&mut self) {
        let dt_str = self.ask("🕒 Enter date/time (YYYY-MM-DD HH:MM) or leave empty for now: ");
        if dt_str.is_empty() {
            self.sky.now = Local::now();
            println!("{}", c("Time set to current.", "dim"));
            return;
        }
        if let Ok(dt) = NaiveDateTime::parse_from_str(&dt_str, "%Y-%m-%d %H:%M") {
            let dt_local = DateTime::from_naive_utc_and_offset(dt, *Local::now().offset());
            self.sky.set_time(dt_local);
            println!("{}", c(&format!("Time set to {}", dt_local.format("%Y-%m-%d %H:%M")), "green"));
        } else {
            println!("{}", c("Invalid format.", "red"));
        }
    }

    fn toggle_favourite(&mut self) {
        let name = self.ask("❤️  Enter star name: ");
        let found = self.sky.stars.iter().find(|s| s.name.to_lowercase() == name.to_lowercase());
        if let Some(s) = found {
            self.user.toggle_favourite(&s.name);
            let state = if self.user.is_favourite(&s.name) { "added to" } else { "removed from" };
            println!("{}", c(&format!("✅ {} {} favourites.", s.name, state), "green"));
        } else {
            println!("{}", c("Star not found.", "red"));
        }
    }

    fn show_favourites(&self) {
        let favs: Vec<&Star> = self.sky.stars.iter()
            .filter(|s| self.user.is_favourite(&s.name))
            .collect();
        if favs.is_empty() {
            println!("{}", c("No favourites.", "yellow"));
            return;
        }
        println!("\n⭐ FAVOURITES");
        for s in favs {
            println!("  {} ({})", s.name, s.constel);
        }
    }

    fn run(&mut self) {
        println!("{}", "\n🌟 Star Map AR – Interactive Night Sky Explorer".bright().cyan());
        println!("{}", "Explore the cosmos from your terminal!".dimmed());

        loop {
            self.show_menu();
            let choice = self.ask("Your choice: ");
            match choice.as_str() {
                "1" => self.show_map(),
                "2" => self.search_star(),
                "3" => self.highlight_constellation(),
                "4" => self.set_location(),
                "5" => self.set_time(),
                "6" => self.toggle_favourite(),
                "7" => self.show_favourites(),
                "0" => {
                    println!("{}", c("👋 Clear skies!", "cyan"));
                    return;
                }
                _ => println!("{}", c("❌ Invalid choice.", "red")),
            }
            if choice != "0" {
                print!("\nPress Enter to continue...");
                io::stdout().flush().unwrap();
                let mut _dummy = String::new();
                io::stdin().read_line(&mut _dummy).unwrap();
            }
        }
    }
}

// ─── Main ────────────────────────────────────────────────────────────────────

fn main() {
    let mut app = StarApp::new();
    app.run();
}
