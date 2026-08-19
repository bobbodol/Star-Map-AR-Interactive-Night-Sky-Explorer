# star_map.go
/**
 * 🌟 Star Map AR – Interactive Night Sky Explorer (Go Edition)
 * Features: ASCII sky map, constellation tracing, star search, favourites, simulation
 */

package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// ─── Star Database ──────────────────────────────────────────────────────────

type Star struct {
	Name   string
	RA     float64 // hours
	Dec    float64 // degrees
	Mag    float64
	Const  string
}

var STARS = []Star{
	{"Sirius", 6.75, -16.72, -1.46, "Canis Major"},
	{"Canopus", 6.40, -52.70, -0.72, "Carina"},
	{"Rigil Kentaurus", 14.65, -60.83, -0.27, "Centaurus"},
	{"Arcturus", 14.25, 19.18, -0.05, "Boötes"},
	{"Vega", 18.62, 38.78, 0.03, "Lyra"},
	{"Capella", 5.27, 46.00, 0.08, "Auriga"},
	{"Rigel", 5.20, -8.20, 0.12, "Orion"},
	{"Procyon", 7.65, 5.23, 0.34, "Canis Minor"},
	{"Achernar", 1.63, -57.24, 0.45, "Eridanus"},
	{"Betelgeuse", 5.92, 7.41, 0.42, "Orion"},
	{"Hadar", 14.08, -60.37, 0.61, "Centaurus"},
	{"Altair", 19.85, 8.87, 0.76, "Aquila"},
	{"Aldebaran", 4.62, 16.51, 0.85, "Taurus"},
	{"Antares", 16.47, -26.43, 0.96, "Scorpius"},
	{"Spica", 13.42, -11.16, 0.98, "Virgo"},
	{"Pollux", 7.75, 28.03, 1.14, "Gemini"},
	{"Fomalhaut", 22.95, -29.62, 1.16, "Piscis Austrinus"},
	{"Deneb", 20.70, 45.28, 1.25, "Cygnus"},
	{"Regulus", 10.15, 11.97, 1.35, "Leo"},
	{"Adhara", 6.93, -29.00, 1.50, "Canis Major"},
	{"Castor", 7.63, 31.87, 1.58, "Gemini"},
	{"Gacrux", 12.47, -57.11, 1.63, "Crux"},
	{"Shaula", 17.48, -37.06, 1.62, "Scorpius"},
	{"Mintaka", 5.53, -0.30, 2.23, "Orion"},
	{"Alnilam", 5.63, -1.20, 1.69, "Orion"},
	{"Alnitak", 5.68, -1.95, 1.74, "Orion"},
	{"Saiph", 5.63, -9.67, 2.06, "Orion"},
	{"Bellatrix", 5.42, 6.35, 1.64, "Orion"},
	{"Alcyone", 3.72, 24.10, 2.87, "Taurus"},
	{"Mirfak", 3.38, 49.86, 1.79, "Perseus"},
	{"Algol", 3.08, 40.95, 2.09, "Perseus"},
	{"Caph", 0.17, 59.15, 2.28, "Cassiopeia"},
	{"Schedar", 0.68, 56.54, 2.24, "Cassiopeia"},
	{"Polaris", 2.52, 89.26, 1.97, "Ursa Minor"},
	{"Alioth", 12.90, 55.96, 1.76, "Ursa Major"},
	{"Dubhe", 11.05, 61.75, 1.79, "Ursa Major"},
	{"Merak", 11.03, 56.38, 2.37, "Ursa Major"},
	{"Phecda", 11.90, 53.69, 2.44, "Ursa Major"},
	{"Megrez", 12.25, 57.03, 3.31, "Ursa Major"},
	{"Mizar", 13.40, 54.93, 2.23, "Ursa Major"},
	{"Alkaid", 13.78, 49.31, 1.85, "Ursa Major"},
	{"Thuban", 14.08, 64.37, 3.65, "Draco"},
	{"Elnath", 5.45, 28.60, 1.65, "Taurus"},
	{"Menkalinan", 6.60, 44.85, 1.90, "Auriga"},
	{"Navi", 1.88, 62.60, 2.15, "Cassiopeia"},
	{"Ruchbah", 1.42, 60.72, 2.68, "Cassiopeia"},
	{"Segin", 1.08, 60.57, 3.37, "Cassiopeia"},
	{"Nihal", 5.75, -20.75, 2.80, "Lepus"},
}

// ─── Colors ──────────────────────────────────────────────────────────────────

const (
	reset  = "\x1b[0m"
	bright = "\x1b[1m"
	dim    = "\x1b[2m"
	red    = "\x1b[31m"
	green  = "\x1b[32m"
	yellow = "\x1b[33m"
	blue   = "\x1b[34m"
	magenta = "\x1b[35m"
	cyan   = "\x1b[36m"
	white  = "\x1b[37m"
)

func c(str, color string) string {
	return color + str + reset
}

// ─── User Data ─────────────────────────────────────────────────────────────

type UserData struct {
	Favourites []string  `json:"favourites"`
	Latitude   float64   `json:"latitude"`
	Longitude  float64   `json:"longitude"`
	Timezone   int       `json:"timezone"`
	filePath   string
}

func NewUserData() *UserData {
	home, _ := os.UserHomeDir()
	dir := filepath.Join(home, ".star_map")
	os.MkdirAll(dir, 0755)
	filePath := filepath.Join(dir, "user.json")
	ud := &UserData{filePath: filePath}
	ud.load()
	return ud
}

func (ud *UserData) load() {
	if _, err := os.Stat(ud.filePath); os.IsNotExist(err) {
		ud.Latitude = 40.7
		ud.Longitude = -74.0
		ud.Timezone = -5
		return
	}
	raw, err := os.ReadFile(ud.filePath)
	if err != nil {
		return
	}
	var data UserData
	if err := json.Unmarshal(raw, &data); err != nil {
		return
	}
	ud.Favourites = data.Favourites
	ud.Latitude = data.Latitude
	ud.Longitude = data.Longitude
	ud.Timezone = data.Timezone
	if ud.Latitude == 0 {
		ud.Latitude = 40.7
	}
	if ud.Longitude == 0 {
		ud.Longitude = -74.0
	}
}

func (ud *UserData) save() {
	raw, _ := json.MarshalIndent(ud, "", "  ")
	os.WriteFile(ud.filePath, raw, 0644)
}

func (ud *UserData) ToggleFavourite(name string) {
	for i, n := range ud.Favourites {
		if n == name {
			ud.Favourites = append(ud.Favourites[:i], ud.Favourites[i+1:]...)
			ud.save()
			return
		}
	}
	ud.Favourites = append(ud.Favourites, name)
	ud.save()
}

func (ud *UserData) IsFavourite(name string) bool {
	for _, n := range ud.Favourites {
		if n == name {
			return true
		}
	}
	return false
}

// ─── Sky Map Engine ─────────────────────────────────────────────────────────

type SkyMap struct {
	latRad    float64
	lonRad    float64
	timezone  int
	now       time.Time
	stars     []Star
}

func NewSkyMap(lat, lon float64, tz int) *SkyMap {
	return &SkyMap{
		latRad:   lat * math.Pi / 180,
		lonRad:   lon * math.Pi / 180,
		timezone: tz,
		now:      time.Now(),
		stars:    STARS,
	}
}

func (sm *SkyMap) SetTime(t time.Time) { sm.now = t }

func (sm *SkyMap) julianDate(t time.Time) float64 {
	year := t.Year()
	month := int(t.Month())
	day := float64(t.Day()) + float64(t.Hour())/24 + float64(t.Minute())/1440 + float64(t.Second())/86400
	if month <= 2 {
		year--
		month += 12
	}
	A := year / 100
	B := 2 - A + A/4
	return float64(int(365.25*float64(year+4716))+int(30.6001*float64(month+1))) + day + float64(B) - 1524.5
}

func (sm *SkyMap) localSiderealTime(t time.Time) float64 {
	jd := sm.julianDate(t)
	gmst := 280.46061837 + 360.98564736629*(jd-2451545.0) + 0.000387933*(jd-2451545.0)*(jd-2451545.0)
	gmst = math.Mod(gmst, 360)
	lst := gmst + sm.lonRad*180/math.Pi
	lst = math.Mod(lst, 360)
	return lst / 15.0
}

func (sm *SkyMap) altaz(raHours, decDeg float64, t time.Time) (alt, az float64) {
	lst := sm.localSiderealTime(t)
	ha := (lst - raHours) * 15 * math.Pi / 180
	dec := decDeg * math.Pi / 180
	lat := sm.latRad
	alt = math.Asin(math.Sin(dec)*math.Sin(lat) + math.Cos(dec)*math.Cos(lat)*math.Cos(ha))
	az = math.Atan2(-math.Sin(ha), math.Tan(dec)*math.Cos(lat)-math.Cos(ha)*math.Sin(lat))
	az = math.Mod(az*180/math.Pi+360, 360)
	alt = alt * 180 / math.Pi
	return
}

type VisibleStar struct {
	Name   string
	RA     float64
	Dec    float64
	Mag    float64
	Const  string
	Alt    float64
	Az     float64
}

func (sm *SkyMap) GetVisibleStars(minAlt float64) []VisibleStar {
	if minAlt == 0 {
		minAlt = -10
	}
	var visible []VisibleStar
	for _, s := range sm.stars {
		alt, az := sm.altaz(s.RA, s.Dec, sm.now)
		if alt > minAlt {
			visible = append(visible, VisibleStar{
				Name:   s.Name,
				RA:     s.RA,
				Dec:    s.Dec,
				Mag:    s.Mag,
				Const:  s.Const,
				Alt:    alt,
				Az:     az,
			})
		}
	}
	return visible
}

func (sm *SkyMap) RenderMap(width, height int, highlightConst string) string {
	if width == 0 {
		width = 50
	}
	if height == 0 {
		height = 20
	}
	visible := sm.GetVisibleStars(-10)
	grid := make([][]string, height)
	for i := range grid {
		grid[i] = make([]string, width)
		for j := range grid[i] {
			grid[i][j] = " "
		}
	}
	altMin := -10.0
	altMax := 90.0
	for _, star := range visible {
		alt := star.Alt
		az := star.Az
		if alt < altMin {
			continue
		}
		row := int((alt - altMin) / (altMax - altMin) * float64(height-1))
		col := int((az / 360) * float64(width)) % width
		mag := star.Mag
		var ch string
		if mag < 0 {
			ch = "●"
		} else if mag < 1 {
			ch = "◉"
		} else if mag < 2 {
			ch = "○"
		} else if mag < 3 {
			ch = "·"
		} else {
			ch = "."
		}
		if highlightConst != "" && strings.EqualFold(star.Const, highlightConst) {
			ch = c(ch, yellow)
		} else {
			ch = c(ch, white)
		}
		grid[row][col] = ch
	}
	var lines []string
	for _, row := range grid {
		lines = append(lines, strings.Join(row, ""))
	}
	return strings.Join(lines, "\n")
}

// ─── Main App ──────────────────────────────────────────────────────────────

type StarApp struct {
	reader         *bufio.Reader
	user           *UserData
	sky            *SkyMap
	highlightConst string
}

func NewStarApp() *StarApp {
	user := NewUserData()
	return &StarApp{
		reader: bufio.NewReader(os.Stdin),
		user:   user,
		sky:    NewSkyMap(user.Latitude, user.Longitude, user.Timezone),
	}
}

func (app *StarApp) ask(prompt string) string {
	fmt.Print(prompt)
	line, _ := app.reader.ReadString('\n')
	return strings.TrimSpace(line)
}

func (app *StarApp) askFloat(prompt string, def float64) float64 {
	for {
		ans := app.ask(prompt)
		if ans == "" {
			return def
		}
		if val, err := strconv.ParseFloat(ans, 64); err == nil {
			return val
		}
		fmt.Println(c("Please enter a number.", yellow))
	}
}

func (app *StarApp) askInt(prompt string, def int) int {
	for {
		ans := app.ask(prompt)
		if ans == "" {
			return def
		}
		if val, err := strconv.Atoi(ans); err == nil {
			return val
		}
		fmt.Println(c("Please enter a number.", yellow))
	}
}

func (app *StarApp) showMenu() {
	fmt.Println("\n" + c(strings.Repeat("═", 50), cyan))
	fmt.Println(c("🌟 STAR MAP AR", bright+cyan))
	fmt.Println(c(strings.Repeat("═", 50), cyan))
	fmt.Printf("  Latitude: %.1f°  Longitude: %.1f°\n", app.user.Latitude, app.user.Longitude)
	fmt.Printf("  Time: %s\n", app.sky.now.Format("2006-01-02 15:04"))
	fmt.Printf("  Highlight: %s\n", app.highlightConst)
	if app.highlightConst == "" {
		fmt.Print("None")
	}
	fmt.Println(c(strings.Repeat("═", 50), cyan))
	fmt.Println("  1. 🌌 Show Sky Map")
	fmt.Println("  2. ⭐ Search Star")
	fmt.Println("  3. 🗺️  Highlight Constellation")
	fmt.Println("  4. 📍 Set Location")
	fmt.Println("  5. 🕒 Set Time")
	fmt.Println("  6. ❤️  Toggle Favourite")
	fmt.Println("  7. 📊 Favourites")
	fmt.Println("  0. 🚪 Exit")
	fmt.Println(c(strings.Repeat("═", 50), cyan))
}

func (app *StarApp) showMap() {
	fmt.Println("\n🌌 Sky Map")
	mapStr := app.sky.RenderMap(50, 20, app.highlightConst)
	fmt.Println(mapStr)
}

func (app *StarApp) searchStar() {
	query := app.ask("⭐ Enter star name or constellation: ")
	var results []Star
	for _, s := range app.sky.stars {
		if strings.Contains(strings.ToLower(s.Name), strings.ToLower(query)) ||
			strings.Contains(strings.ToLower(s.Const), strings.ToLower(query)) {
			results = append(results, s)
		}
	}
	if len(results) == 0 {
		fmt.Println(c("No stars found.", yellow))
		return
	}
	fmt.Printf("\n🔍 Results (%d)\n", len(results))
	for _, s := range results {
		fav := " "
		if app.user.IsFavourite(s.Name) {
			fav = "⭐"
		}
		fmt.Printf("  %s %s  RA:%.2fh  Dec:%.2f°  Mag:%.2f  %s\n", fav, s.Name, s.RA, s.Dec, s.Mag, s.Const)
	}
}

func (app *StarApp) highlightConstellation() {
	constel := app.ask("🗺️  Constellation name (or 'none' to clear): ")
	if strings.EqualFold(constel, "none") {
		app.highlightConst = ""
		fmt.Println(c("Highlight cleared.", dim))
		return
	}
	exists := false
	for _, s := range app.sky.stars {
		if strings.EqualFold(s.Const, constel) {
			exists = true
			break
		}
	}
	if !exists {
		fmt.Println(c("Constellation not found.", red))
		return
	}
	app.highlightConst = constel
	fmt.Printf("%s\n", c("Highlighting "+constel, green))
}

func (app *StarApp) setLocation() {
	lat := app.askFloat("📍 Latitude (default "+fmt.Sprintf("%.1f", app.user.Latitude)+"): ", app.user.Latitude)
	lon := app.askFloat("📍 Longitude (default "+fmt.Sprintf("%.1f", app.user.Longitude)+"): ", app.user.Longitude)
	tz := app.askInt("🕒 Timezone offset (default "+fmt.Sprintf("%d", app.user.Timezone)+"): ", app.user.Timezone)
	if lat < -90 || lat > 90 || lon < -180 || lon > 180 || tz < -12 || tz > 14 {
		fmt.Println(c("Invalid values.", red))
		return
	}
	app.user.Latitude = lat
	app.user.Longitude = lon
	app.user.Timezone = tz
	app.user.save()
	app.sky = NewSkyMap(lat, lon, tz)
	fmt.Println(c("✅ Location updated.", green))
}

func (app *StarApp) setTime() {
	dtStr := app.ask("🕒 Enter date/time (YYYY-MM-DD HH:MM) or leave empty for now: ")
	if dtStr == "" {
		app.sky.now = time.Now()
		fmt.Println(c("Time set to current.", dim))
		return
	}
	dt, err := time.Parse("2006-01-02 15:04", dtStr)
	if err != nil {
		fmt.Println(c("Invalid format.", red))
		return
	}
	app.sky.SetTime(dt)
	fmt.Printf("%s\n", c("Time set to "+dt.Format("2006-01-02 15:04"), green))
}

func (app *StarApp) toggleFavourite() {
	name := app.ask("❤️  Enter star name: ")
	var found *Star
	for _, s := range app.sky.stars {
		if strings.EqualFold(s.Name, name) {
			found = &s
			break
		}
	}
	if found == nil {
		fmt.Println(c("Star not found.", red))
		return
	}
	app.user.ToggleFavourite(found.Name)
	state := "removed from"
	if app.user.IsFavourite(found.Name) {
		state = "added to"
	}
	fmt.Printf("%s\n", c("✅ "+found.Name+" "+state+" favourites.", green))
}

func (app *StarApp) showFavourites() {
	var favs []Star
	for _, s := range app.sky.stars {
		if app.user.IsFavourite(s.Name) {
			favs = append(favs, s)
		}
	}
	if len(favs) == 0 {
		fmt.Println(c("No favourites.", yellow))
		return
	}
	fmt.Println("\n⭐ FAVOURITES")
	for _, s := range favs {
		fmt.Printf("  %s (%s)\n", s.Name, s.Const)
	}
}

func (app *StarApp) run() {
	fmt.Print("\033[H\033[2J")
	fmt.Printf("%s\n", c("\n🌟 Star Map AR – Interactive Night Sky Explorer", bright+cyan))
	fmt.Printf("%s\n", c("Explore the cosmos from your terminal!", dim))

	for {
		app.showMenu()
		choice := app.ask("Your choice: ")
		switch choice {
		case "1":
			app.showMap()
		case "2":
			app.searchStar()
		case "3":
			app.highlightConstellation()
		case "4":
			app.setLocation()
		case "5":
			app.setTime()
		case "6":
			app.toggleFavourite()
		case "7":
			app.showFavourites()
		case "0":
			fmt.Printf("%s\n", c("👋 Clear skies!", cyan))
			return
		default:
			fmt.Println(c("❌ Invalid choice.", red))
		}
		if choice != "0" {
			fmt.Print("\nPress Enter to continue...")
			app.reader.ReadString('\n')
		}
	}
}

func main() {
	app := NewStarApp()
	app.run()
}
