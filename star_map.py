# star_map.py
#!/usr/bin/env python3
"""
🌟 Star Map AR – Interactive Night Sky Explorer (Python Edition)
Features: ASCII sky map, constellation tracing, star search, favourites, real‑time simulation
"""

import json
import math
import os
import sys
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Install 'rich' for enhanced UI: pip install rich")

# ─── Colors ──────────────────────────────────────────────────────────────────

def c(text: str, color: str) -> str:
    colors = {
        "reset": "\033[0m", "bright": "\033[1m", "dim": "\033[2m",
        "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
        "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
        "white": "\033[37m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"

# ─── Star Database ──────────────────────────────────────────────────────────

STARS = [
    # Name, RA (hours), Dec (degrees), Magnitude, Constellation
    ("Sirius", 6.75, -16.72, -1.46, "Canis Major"),
    ("Canopus", 6.40, -52.70, -0.72, "Carina"),
    ("Rigil Kentaurus", 14.65, -60.83, -0.27, "Centaurus"),
    ("Arcturus", 14.25, 19.18, -0.05, "Boötes"),
    ("Vega", 18.62, 38.78, 0.03, "Lyra"),
    ("Capella", 5.27, 46.00, 0.08, "Auriga"),
    ("Rigel", 5.20, -8.20, 0.12, "Orion"),
    ("Procyon", 7.65, 5.23, 0.34, "Canis Minor"),
    ("Achernar", 1.63, -57.24, 0.45, "Eridanus"),
    ("Betelgeuse", 5.92, 7.41, 0.42, "Orion"),
    ("Hadar", 14.08, -60.37, 0.61, "Centaurus"),
    ("Altair", 19.85, 8.87, 0.76, "Aquila"),
    ("Aldebaran", 4.62, 16.51, 0.85, "Taurus"),
    ("Antares", 16.47, -26.43, 0.96, "Scorpius"),
    ("Spica", 13.42, -11.16, 0.98, "Virgo"),
    ("Pollux", 7.75, 28.03, 1.14, "Gemini"),
    ("Fomalhaut", 22.95, -29.62, 1.16, "Piscis Austrinus"),
    ("Deneb", 20.70, 45.28, 1.25, "Cygnus"),
    ("Regulus", 10.15, 11.97, 1.35, "Leo"),
    ("Adhara", 6.93, -29.00, 1.50, "Canis Major"),
    ("Castor", 7.63, 31.87, 1.58, "Gemini"),
    ("Gacrux", 12.47, -57.11, 1.63, "Crux"),
    ("Shaula", 17.48, -37.06, 1.62, "Scorpius"),
    ("Mintaka", 5.53, -0.30, 2.23, "Orion"),
    ("Alnilam", 5.63, -1.20, 1.69, "Orion"),
    ("Alnitak", 5.68, -1.95, 1.74, "Orion"),
    ("Saiph", 5.63, -9.67, 2.06, "Orion"),
    ("Bellatrix", 5.42, 6.35, 1.64, "Orion"),
    ("Alcyone", 3.72, 24.10, 2.87, "Taurus"),
    ("Mirfak", 3.38, 49.86, 1.79, "Perseus"),
    ("Algol", 3.08, 40.95, 2.09, "Perseus"),
    ("Caph", 0.17, 59.15, 2.28, "Cassiopeia"),
    ("Schedar", 0.68, 56.54, 2.24, "Cassiopeia"),
    ("Polaris", 2.52, 89.26, 1.97, "Ursa Minor"),
    ("Alioth", 12.90, 55.96, 1.76, "Ursa Major"),
    ("Dubhe", 11.05, 61.75, 1.79, "Ursa Major"),
    ("Merak", 11.03, 56.38, 2.37, "Ursa Major"),
    ("Phecda", 11.90, 53.69, 2.44, "Ursa Major"),
    ("Megrez", 12.25, 57.03, 3.31, "Ursa Major"),
    ("Mizar", 13.40, 54.93, 2.23, "Ursa Major"),
    ("Alkaid", 13.78, 49.31, 1.85, "Ursa Major"),
    ("Thuban", 14.08, 64.37, 3.65, "Draco"),
    ("Elnath", 5.45, 28.60, 1.65, "Taurus"),
    ("Menkalinan", 6.60, 44.85, 1.90, "Auriga"),
    ("Navi", 1.88, 62.60, 2.15, "Cassiopeia"),
    ("Ruchbah", 1.42, 60.72, 2.68, "Cassiopeia"),
    ("Segin", 1.08, 60.57, 3.37, "Cassiopeia"),
    ("Nihal", 5.75, -20.75, 2.80, "Lepus"),
]

# Constellation lines: list of pairs of star indices that form constellation lines
CONSTELLATION_LINES = [
    # Orion
    (6, 21), (6, 23), (23, 24), (24, 25), (25, 6),  # Belt
    (6, 28), (6, 29), (21, 29), (23, 28),  # Body
    # Ursa Major
    (34, 35), (35, 36), (36, 37), (37, 38), (38, 39), (39, 40),  # Big Dipper
    # Cassiopeia
    (31, 32), (32, 43), (43, 44), (44, 45),  # W shape
    # Lyra
    (4,),  # Single star Vega
    # Scorpius
    (13,),  # Antares
    # Boötes
    (3,),  # Arcturus
    # Leo
    (18,),  # Regulus
]

# ─── User Data ──────────────────────────────────────────────────────────────

class UserData:
    DATA_DIR = Path.home() / ".star_map"
    DATA_FILE = DATA_DIR / "user.json"

    def __init__(self):
        self.favourites: List[str] = []
        self.latitude = 40.7
        self.longitude = -74.0
        self.timezone = -5
        self._load()

    def _load(self):
        if self.DATA_FILE.exists():
            try:
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.favourites = data.get("favourites", [])
                    self.latitude = data.get("latitude", 40.7)
                    self.longitude = data.get("longitude", -74.0)
                    self.timezone = data.get("timezone", -5)
            except Exception:
                pass

    def save(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.DATA_FILE, 'w') as f:
            json.dump({
                "favourites": self.favourites,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "timezone": self.timezone
            }, f, indent=2)

    def toggle_favourite(self, name: str):
        if name in self.favourites:
            self.favourites.remove(name)
        else:
            self.favourites.append(name)
        self.save()

    def is_favourite(self, name: str) -> bool:
        return name in self.favourites

# ─── Sky Map Engine ─────────────────────────────────────────────────────────

class SkyMap:
    def __init__(self, latitude: float = 40.7, longitude: float = -74.0, timezone: int = -5):
        self.latitude = math.radians(latitude)
        self.longitude = math.radians(longitude)
        self.timezone = timezone
        self.stars = [(name, ra, dec, mag, const) for name, ra, dec, mag, const in STARS]
        self.now = datetime.now()

    def set_time(self, dt: datetime):
        self.now = dt

    def _julian_date(self, dt: datetime) -> float:
        # Simplified Julian date (approximate)
        year = dt.year
        month = dt.month
        day = dt.day + dt.hour / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
        if month <= 2:
            year -= 1
            month += 12
        A = int(year / 100)
        B = 2 - A + int(A / 4)
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5

    def _local_sidereal_time(self, dt: datetime) -> float:
        # Compute Local Sidereal Time (hours)
        jd = self._julian_date(dt)
        gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * ((jd - 2451545.0) ** 2)
        gmst = gmst % 360
        lst = gmst + math.degrees(self.longitude)
        lst = lst % 360
        return lst / 15.0  # hours

    def _altaz(self, ra_hours: float, dec_deg: float, dt: datetime) -> Tuple[float, float]:
        # Convert RA/Dec to Altitude/Azimuth (degrees)
        lst = self._local_sidereal_time(dt)
        ha = math.radians((lst - ra_hours) * 15)
        dec = math.radians(dec_deg)
        lat = self.latitude
        alt = math.asin(math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha))
        az = math.atan2(-math.sin(ha), math.tan(dec) * math.cos(lat) - math.cos(ha) * math.sin(lat))
        return math.degrees(alt), (math.degrees(az) % 360)

    def get_visible_stars(self, min_alt: float = -10) -> List[Dict]:
        visible = []
        for name, ra, dec, mag, const in self.stars:
            alt, az = self._altaz(ra, dec, self.now)
            if alt > min_alt:
                visible.append({
                    "name": name,
                    "ra": ra,
                    "dec": dec,
                    "mag": mag,
                    "const": const,
                    "alt": alt,
                    "az": az
                })
        return visible

    def render_map(self, width: int = 50, height: int = 20, highlight_const: str = None) -> str:
        """Render ASCII sky map with stars."""
        visible = self.get_visible_stars()
        # Create grid (height rows, width cols)
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        # Map altitude -10 to 90 degrees to grid rows
        alt_min = -10
        alt_max = 90
        # Azimuth 0-360 maps to cols (wrap)
        for star in visible:
            alt = star["alt"]
            az = star["az"]
            if alt < alt_min:
                continue
            row = int((alt - alt_min) / (alt_max - alt_min) * (height - 1))
            col = int((az / 360) * width) % width
            # Magnitude to brightness
            mag = star["mag"]
            if mag < 0:
                ch = '●'
            elif mag < 1:
                ch = '◉'
            elif mag < 2:
                ch = '○'
            elif mag < 3:
                ch = '·'
            else:
                ch = '.'
            # Set colour based on star temperature? Just use white for now.
            # Highlight constellation if specified
            if highlight_const and star["const"].lower() == highlight_const.lower():
                ch = c(ch, "yellow")
            else:
                ch = c(ch, "white")
            grid[row][col] = ch
        # Add constellation lines (simplified: draw lines between stars)
        # For simplicity, we'll skip drawing lines in this demo.
        # Return rendered map as string
        lines = []
        for row in grid:
            lines.append(''.join(row))
        return '\n'.join(lines)

# ─── Main App ──────────────────────────────────────────────────────────────

class StarApp:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.user = UserData()
        self.sky = SkyMap(self.user.latitude, self.user.longitude, self.user.timezone)
        self.highlight_const = None

    def show_menu(self):
        if self.console:
            panel = Panel(
                f"[bold cyan]🌟 Star Map AR[/bold cyan]\n"
                f"  Latitude: {self.user.latitude:.1f}°  Longitude: {self.user.longitude:.1f}°\n"
                f"  Time: {self.sky.now.strftime('%Y-%m-%d %H:%M')}\n"
                f"  Highlight: {self.highlight_const or 'None'}",
                title="📋 Main Menu",
                border_style="blue"
            )
            self.console.print(panel)
            self.console.print(" [1] 🌌 Show Sky Map")
            self.console.print(" [2] ⭐ Search Star")
            self.console.print(" [3] 🗺️  Highlight Constellation")
            self.console.print(" [4] 📍 Set Location")
            self.console.print(" [5] 🕒 Set Time")
            self.console.print(" [6] ❤️  Toggle Favourite")
            self.console.print(" [7] 📊 Favourites")
            self.console.print(" [0] 🚪 Exit")
        else:
            print("\n" + "="*50)
            print(c("🌟 STAR MAP AR", "bright"))
            print("="*50)
            print(f"  Latitude: {self.user.latitude:.1f}°  Longitude: {self.user.longitude:.1f}°")
            print(f"  Time: {self.sky.now.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Highlight: {self.highlight_const or 'None'}")
            print("="*50)
            print("  1. 🌌 Show Sky Map")
            print("  2. ⭐ Search Star")
            print("  3. 🗺️  Highlight Constellation")
            print("  4. 📍 Set Location")
            print("  5. 🕒 Set Time")
            print("  6. ❤️  Toggle Favourite")
            print("  7. 📊 Favourites")
            print("  0. 🚪 Exit")
            print("="*50)

    def show_map(self):
        if self.console:
            self.console.print("\n[bold]🌌 Sky Map[/bold]")
            map_str = self.sky.render_map(highlight_const=self.highlight_const)
            self.console.print(Panel(map_str, title="Star Map", border_style="cyan"))
        else:
            print("\n🌌 Sky Map")
            print(self.sky.render_map(highlight_const=self.highlight_const))

    def search_star(self):
        if self.console:
            query = Prompt.ask("⭐ Enter star name or constellation")
        else:
            query = input("⭐ Enter star name or constellation: ").strip()
        results = []
        for name, ra, dec, mag, const in self.sky.stars:
            if query.lower() in name.lower() or query.lower() in const.lower():
                results.append((name, ra, dec, mag, const))
        if not results:
            print(c("No stars found.", "yellow"))
            return
        if self.console:
            table = Table(title=f"🔍 Results ({len(results)})", box=box.ROUNDED)
            table.add_column("Name", style="green")
            table.add_column("RA (h)", style="cyan")
            table.add_column("Dec (°)", style="cyan")
            table.add_column("Mag", justify="right")
            table.add_column("Constellation")
            for name, ra, dec, mag, const in results:
                fav = "⭐" if self.user.is_favourite(name) else ""
                table.add_row(name + fav, f"{ra:.2f}", f"{dec:.2f}", f"{mag:.2f}", const)
            self.console.print(table)
        else:
            print(f"\n🔍 Results ({len(results)})")
            for name, ra, dec, mag, const in results:
                fav = "⭐" if self.user.is_favourite(name) else ""
                print(f"  {fav} {name}  RA:{ra:.2f}h  Dec:{dec:.2f}°  Mag:{mag:.2f}  {const}")

    def highlight_constellation(self):
        if self.console:
            const = Prompt.ask("🗺️  Constellation name to highlight (or 'none' to clear)")
        else:
            const = input("🗺️  Constellation name (or 'none' to clear): ").strip()
        if const.lower() == "none":
            self.highlight_const = None
            print(c("Highlight cleared.", "dim"))
            return
        # Check if constellation exists in stars
        exists = any(const.lower() == c.lower() for _, _, _, _, c in self.sky.stars)
        if not exists:
            print(c("Constellation not found.", "red"))
            return
        self.highlight_const = const
        print(c(f"Highlighting {const}", "green"))

    def set_location(self):
        if self.console:
            lat = FloatPrompt.ask("📍 Latitude (degrees, -90 to 90)", default=self.user.latitude)
            lon = FloatPrompt.ask("📍 Longitude (degrees, -180 to 180)", default=self.user.longitude)
            tz = IntPrompt.ask("🕒 Timezone offset (hours, -12 to 14)", default=self.user.timezone)
        else:
            try:
                lat = float(input(f"Latitude (default {self.user.latitude}): ") or self.user.latitude)
                lon = float(input(f"Longitude (default {self.user.longitude}): ") or self.user.longitude)
                tz = int(input(f"Timezone offset (default {self.user.timezone}): ") or self.user.timezone)
            except ValueError:
                print(c("Invalid input. Keeping current settings.", "yellow"))
                return
        if lat < -90 or lat > 90 or lon < -180 or lon > 180 or tz < -12 or tz > 14:
            print(c("Invalid values.", "red"))
            return
        self.user.latitude = lat
        self.user.longitude = lon
        self.user.timezone = tz
        self.user.save()
        self.sky = SkyMap(lat, lon, tz)
        print(c("✅ Location updated.", "green"))

    def set_time(self):
        if self.console:
            dt_str = Prompt.ask("🕒 Enter date/time (YYYY-MM-DD HH:MM) or leave empty for now")
        else:
            dt_str = input("🕒 Enter date/time (YYYY-MM-DD HH:MM) or leave empty for now: ").strip()
        if not dt_str:
            self.sky.now = datetime.now()
            print(c("Time set to current.", "dim"))
            return
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            self.sky.set_time(dt)
            print(c(f"Time set to {dt.strftime('%Y-%m-%d %H:%M')}", "green"))
        except ValueError:
            print(c("Invalid format. Use YYYY-MM-DD HH:MM", "red"))

    def toggle_favourite(self):
        if self.console:
            name = Prompt.ask("❤️  Enter star name to toggle favourite")
        else:
            name = input("❤️  Enter star name: ").strip()
        # Find exact match
        found = None
        for n, _, _, _, _ in self.sky.stars:
            if n.lower() == name.lower():
                found = n
                break
        if not found:
            print(c("Star not found.", "red"))
            return
        self.user.toggle_favourite(found)
        state = "added to" if self.user.is_favourite(found) else "removed from"
        print(c(f"✅ {found} {state} favourites.", "green"))

    def show_favourites(self):
        favs = [n for n in self.user.favourites if any(n.lower() == s[0].lower() for s in self.sky.stars)]
        if not favs:
            print(c("No favourites.", "yellow"))
            return
        if self.console:
            table = Table(title="⭐ Favourites", box=box.ROUNDED)
            table.add_column("Name", style="green")
            table.add_column("Constellation", style="cyan")
            for name in favs:
                const = next((c for n, _, _, _, c in self.sky.stars if n == name), "")
                table.add_row(name, const)
            self.console.print(table)
        else:
            print("\n⭐ FAVOURITES")
            for name in favs:
                const = next((c for n, _, _, _, c in self.sky.stars if n == name), "")
                print(f"  {name} ({const})")

    def run(self):
        if self.console:
            self.console.print(Panel.fit("[bold cyan]🌟 Star Map AR – Interactive Night Sky Explorer[/bold cyan]", border_style="cyan"))
        else:
            print(c("\n🌟 Star Map AR – Interactive Night Sky Explorer", "bright"))
            print(c("Explore the cosmos from your terminal!", "dim"))

        while True:
            self.show_menu()
            if self.console:
                choice = Prompt.ask("Your choice", choices=["0","1","2","3","4","5","6","7"])
            else:
                choice = input("Your choice: ").strip()

            if choice == "1":
                self.show_map()
            elif choice == "2":
                self.search_star()
            elif choice == "3":
                self.highlight_constellation()
            elif choice == "4":
                self.set_location()
            elif choice == "5":
                self.set_time()
            elif choice == "6":
                self.toggle_favourite()
            elif choice == "7":
                self.show_favourites()
            elif choice == "0":
                print(c("👋 Clear skies!", "cyan"))
                break
            else:
                print(c("❌ Invalid choice.", "red"))

            if choice != "0":
                if self.console:
                    self.console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()
                else:
                    input("\nPress Enter to continue...")

def main():
    try:
        app = StarApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Clear skies!")
        sys.exit(0)
    except Exception as e:
        print(c(f"❌ Unexpected error: {e}", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
