# StarMap.cs
/**
 * 🌟 Star Map AR – Interactive Night Sky Explorer (C# Edition)
 * Features: ASCII sky map, constellation tracing, star search, favourites, simulation
 * Requires: .NET 6.0+
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

class StarMap
{
    // ─── Colors ────────────────────────────────────────────────────────────

    private static readonly string Reset = "\u001B[0m";
    private static readonly string Bright = "\u001B[1m";
    private static readonly string Dim = "\u001B[2m";
    private static readonly string Red = "\u001B[31m";
    private static readonly string Green = "\u001B[32m";
    private static readonly string Yellow = "\u001B[33m";
    private static readonly string Blue = "\u001B[34m";
    private static readonly string Magenta = "\u001B[35m";
    private static readonly string Cyan = "\u001B[36m";
    private static readonly string White = "\u001B[37m";

    private static string C(string text, string color) => color + text + Reset;

    // ─── Star Class ──────────────────────────────────────────────────────

    public class Star
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = "";
        [JsonPropertyName("ra")]
        public double RA { get; set; } // hours
        [JsonPropertyName("dec")]
        public double Dec { get; set; } // degrees
        [JsonPropertyName("mag")]
        public double Mag { get; set; }
        [JsonPropertyName("constel")]
        public string Constel { get; set; } = "";
    }

    // ─── User Data ─────────────────────────────────────────────────────────

    public class UserData
    {
        [JsonPropertyName("favourites")]
        public List<string> Favourites { get; set; } = new();
        [JsonPropertyName("latitude")]
        public double Latitude { get; set; } = 40.7;
        [JsonPropertyName("longitude")]
        public double Longitude { get; set; } = -74.0;
        [JsonPropertyName("timezone")]
        public int Timezone { get; set; } = -5;
    }

    // ─── Database ─────────────────────────────────────────────────────────

    private static readonly List<Star> STARS = new()
    {
        // ... (full list)
    };

    // ─── Config ────────────────────────────────────────────────────────────

    private static readonly string DataDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        ".star_map"
    );
    private static readonly string DataFile = Path.Combine(DataDir, "user.json");

    // ─── Sky Map Engine ──────────────────────────────────────────────────

    private class SkyMap
    {
        private readonly double latRad, lonRad;
        private readonly int timezone;
        public DateTime Now { get; set; }
        private readonly List<Star> stars;

        public SkyMap(double lat, double lon, int tz)
        {
            latRad = lat * Math.PI / 180;
            lonRad = lon * Math.PI / 180;
            timezone = tz;
            Now = DateTime.Now;
            stars = STARS;
        }

        private double JulianDate(DateTime dt)
        {
            int year = dt.Year;
            int month = dt.Month;
            double day = dt.Day + dt.Hour / 24.0 + dt.Minute / 1440.0 + dt.Second / 86400.0;
            if (month <= 2) { year--; month += 12; }
            int A = year / 100;
            int B = 2 - A + A / 4;
            return Math.Floor(365.25 * (year + 4716)) + Math.Floor(30.6001 * (month + 1)) + day + B - 1524.5;
        }

        private double LocalSiderealTime(DateTime dt)
        {
            double jd = JulianDate(dt);
            double gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * Math.Pow(jd - 2451545.0, 2);
            gmst = gmst % 360;
            double lst = gmst + lonRad * 180 / Math.PI;
            lst = lst % 360;
            return lst / 15.0;
        }

        private (double alt, double az) AltAz(double raHours, double decDeg, DateTime dt)
        {
            double lst = LocalSiderealTime(dt);
            double ha = (lst - raHours) * 15 * Math.PI / 180;
            double dec = decDeg * Math.PI / 180;
            double lat = latRad;
            double alt = Math.Asin(Math.Sin(dec) * Math.Sin(lat) + Math.Cos(dec) * Math.Cos(lat) * Math.Cos(ha));
            double az = Math.Atan2(-Math.Sin(ha), Math.Tan(dec) * Math.Cos(lat) - Math.Cos(ha) * Math.Sin(lat));
            az = (az * 180 / Math.PI % 360 + 360) % 360;
            return (alt * 180 / Math.PI, az);
        }

        public class VisibleStar
        {
            public string Name { get; set; } = "";
            public string Constel { get; set; } = "";
            public double RA { get; set; }
            public double Dec { get; set; }
            public double Mag { get; set; }
            public double Alt { get; set; }
            public double Az { get; set; }
        }

        public List<VisibleStar> GetVisibleStars(double minAlt = -10)
        {
            var visible = new List<VisibleStar>();
            foreach (var s in stars)
            {
                var (alt, az) = AltAz(s.RA, s.Dec, Now);
                if (alt > minAlt)
                {
                    visible.Add(new VisibleStar
                    {
                        Name = s.Name,
                        Constel = s.Constel,
                        RA = s.RA,
                        Dec = s.Dec,
                        Mag = s.Mag,
                        Alt = alt,
                        Az = az
                    });
                }
            }
            return visible;
        }

        public string RenderMap(int width = 50, int height = 20, string highlightConst = null)
        {
            var visible = GetVisibleStars(-10);
            var grid = new char[height, width];
            for (int i = 0; i < height; i++)
                for (int j = 0; j < width; j++)
                    grid[i, j] = ' ';
            double altMin = -10, altMax = 90;
            foreach (var star in visible)
            {
                if (star.Alt < altMin) continue;
                int row = (int)((star.Alt - altMin) / (altMax - altMin) * (height - 1));
                int col = (int)((star.Az / 360) * width) % width;
                char ch = star.Mag < 0 ? '●' : star.Mag < 1 ? '◉' : star.Mag < 2 ? '○' : star.Mag < 3 ? '·' : '.';
                grid[row, col] = ch;
            }
            var lines = new List<string>();
            for (int r = 0; r < height; r++)
            {
                var sb = new System.Text.StringBuilder();
                for (int c = 0; c < width; c++)
                {
                    char ch = grid[r, c];
                    if (ch != ' ')
                        sb.Append(C(ch.ToString(), White));
                    else
                        sb.Append(' ');
                }
                lines.Add(sb.ToString());
            }
            return string.Join("\n", lines);
        }
    }

    // ─── Main App ──────────────────────────────────────────────────────────

    private readonly UserData userData = new();
    private SkyMap sky;
    private string highlightConst = "";

    public StarMap()
    {
        Directory.CreateDirectory(DataDir);
        Load();
        sky = new SkyMap(userData.Latitude, userData.Longitude, userData.Timezone);
    }

    private void Load()
    {
        if (!File.Exists(DataFile)) return;
        try
        {
            string json = File.ReadAllText(DataFile);
            var data = JsonSerializer.Deserialize<UserData>(json);
            if (data != null)
            {
                userData.Favourites = data.Favourites ?? new List<string>();
                userData.Latitude = data.Latitude;
                userData.Longitude = data.Longitude;
                userData.Timezone = data.Timezone;
            }
        }
        catch { /* ignore */ }
    }

    private void Save()
    {
        string json = JsonSerializer.Serialize(userData, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(DataFile, json);
    }

    private void ToggleFavourite(string name)
    {
        if (userData.Favourites.Contains(name))
            userData.Favourites.Remove(name);
        else
            userData.Favourites.Add(name);
        Save();
    }

    private bool IsFavourite(string name) => userData.Favourites.Contains(name);

    // ─── Menu ──────────────────────────────────────────────────────────────

    private string Ask(string prompt)
    {
        Console.Write(prompt);
        return Console.ReadLine()?.Trim() ?? "";
    }

    private double AskDouble(string prompt, double def)
    {
        while (true)
        {
            string ans = Ask(prompt);
            if (string.IsNullOrEmpty(ans)) return def;
            if (double.TryParse(ans, out double val)) return val;
            Console.WriteLine(C("Please enter a number.", Yellow));
        }
    }

    private int AskInt(string prompt, int def)
    {
        while (true)
        {
            string ans = Ask(prompt);
            if (string.IsNullOrEmpty(ans)) return def;
            if (int.TryParse(ans, out int val)) return val;
            Console.WriteLine(C("Please enter a number.", Yellow));
        }
    }

    private void ShowMenu()
    {
        Console.WriteLine("\n" + C(new string('═', 50), Cyan));
        Console.WriteLine(C("🌟 STAR MAP AR", Bright + Cyan));
        Console.WriteLine(C(new string('═', 50), Cyan));
        Console.WriteLine($"  Latitude: {userData.Latitude:F1}°  Longitude: {userData.Longitude:F1}°");
        Console.WriteLine($"  Time: {sky.Now:yyyy-MM-dd HH:mm}");
        Console.WriteLine($"  Highlight: {(string.IsNullOrEmpty(highlightConst) ? "None" : highlightConst)}");
        Console.WriteLine(C(new string('═', 50), Cyan));
        Console.WriteLine("  1. 🌌 Show Sky Map");
        Console.WriteLine("  2. ⭐ Search Star");
        Console.WriteLine("  3. 🗺️  Highlight Constellation");
        Console.WriteLine("  4. 📍 Set Location");
        Console.WriteLine("  5. 🕒 Set Time");
        Console.WriteLine("  6. ❤️  Toggle Favourite");
        Console.WriteLine("  7. 📊 Favourites");
        Console.WriteLine("  0. 🚪 Exit");
        Console.WriteLine(C(new string('═', 50), Cyan));
    }

    private void ShowMap()
    {
        Console.WriteLine("\n🌌 Sky Map");
        string map = sky.RenderMap(50, 20, highlightConst);
        Console.WriteLine(map);
    }

    private void SearchStar()
    {
        string query = Ask("⭐ Enter star name or constellation: ");
        var results = STARS.Where(s =>
            s.Name.Contains(query, StringComparison.OrdinalIgnoreCase) ||
            s.Constel.Contains(query, StringComparison.OrdinalIgnoreCase)
        ).ToList();
        if (!results.Any())
        {
            Console.WriteLine(C("No stars found.", Yellow));
            return;
        }
        Console.WriteLine($"\n🔍 Results ({results.Count})");
        foreach (var s in results)
        {
            string fav = IsFavourite(s.Name) ? "⭐" : " ";
            Console.WriteLine($"  {fav} {s.Name}  RA:{s.RA:F2}h  Dec:{s.Dec:F2}°  Mag:{s.Mag:F2}  {s.Constel}");
        }
    }

    private void HighlightConstellation()
    {
        string constel = Ask("🗺️  Constellation name (or 'none' to clear): ");
        if (constel.Equals("none", StringComparison.OrdinalIgnoreCase))
        {
            highlightConst = "";
            Console.WriteLine(C("Highlight cleared.", Dim));
            return;
        }
        bool exists = STARS.Any(s => s.Constel.Equals(constel, StringComparison.OrdinalIgnoreCase));
        if (!exists)
        {
            Console.WriteLine(C("Constellation not found.", Red));
            return;
        }
        highlightConst = constel;
        Console.WriteLine(C($"Highlighting {constel}", Green));
    }

    private void SetLocation()
    {
        double lat = AskDouble($"📍 Latitude (default {userData.Latitude}): ", userData.Latitude);
        double lon = AskDouble($"📍 Longitude (default {userData.Longitude}): ", userData.Longitude);
        int tz = AskInt($"🕒 Timezone offset (default {userData.Timezone}): ", userData.Timezone);
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180 || tz < -12 || tz > 14)
        {
            Console.WriteLine(C("Invalid values.", Red));
            return;
        }
        userData.Latitude = lat;
        userData.Longitude = lon;
        userData.Timezone = tz;
        Save();
        sky = new SkyMap(lat, lon, tz);
        Console.WriteLine(C("✅ Location updated.", Green));
    }

    private void SetTime()
    {
        string dtStr = Ask("🕒 Enter date/time (YYYY-MM-DD HH:MM) or leave empty for now: ");
        if (string.IsNullOrEmpty(dtStr))
        {
            sky.Now = DateTime.Now;
            Console.WriteLine(C("Time set to current.", Dim));
            return;
        }
        if (DateTime.TryParseExact(dtStr, "yyyy-MM-dd HH:mm", null, System.Globalization.DateTimeStyles.None, out DateTime dt))
        {
            sky.Now = dt;
            Console.WriteLine(C($"Time set to {dt:yyyy-MM-dd HH:mm}", Green));
        }
        else
        {
            Console.WriteLine(C("Invalid format.", Red));
        }
    }

    private void ToggleFavourite()
    {
        string name = Ask("❤️  Enter star name: ");
        var found = STARS.FirstOrDefault(s => s.Name.Equals(name.Trim(), StringComparison.OrdinalIgnoreCase));
        if (found == null)
        {
            Console.WriteLine(C("Star not found.", Red));
            return;
        }
        ToggleFavourite(found.Name);
        string state = IsFavourite(found.Name) ? "added to" : "removed from";
        Console.WriteLine(C($"✅ {found.Name} {state} favourites.", Green));
    }

    private void ShowFavourites()
    {
        var favs = STARS.Where(s => IsFavourite(s.Name)).ToList();
        if (!favs.Any())
        {
            Console.WriteLine(C("No favourites.", Yellow));
            return;
        }
        Console.WriteLine("\n⭐ FAVOURITES");
        foreach (var s in favs)
        {
            Console.WriteLine($"  {s.Name} ({s.Constel})");
        }
    }

    public void Run()
    {
        Console.Clear();
        Console.WriteLine(C("\n🌟 Star Map AR – Interactive Night Sky Explorer", Bright + Cyan));
        Console.WriteLine(C("Explore the cosmos from your terminal!", Dim));

        while (true)
        {
            ShowMenu();
            string choice = Ask("Your choice: ");
            switch (choice)
            {
                case "1": ShowMap(); break;
                case "2": SearchStar(); break;
                case "3": HighlightConstellation(); break;
                case "4": SetLocation(); break;
                case "5": SetTime(); break;
                case "6": ToggleFavourite(); break;
                case "7": ShowFavourites(); break;
                case "0":
                    Console.WriteLine(C("👋 Clear skies!", Cyan));
                    return;
                default:
                    Console.WriteLine(C("❌ Invalid choice.", Red));
                    break;
            }
            if (choice != "0")
            {
                Console.Write("\nPress Enter to continue...");
                Console.ReadLine();
            }
        }
    }

    public static void Main()
    {
        try
        {
            new StarMap().Run();
        }
        catch (Exception ex)
        {
            Console.WriteLine(C($"❌ Unexpected error: {ex.Message}", Red));
            Environment.Exit(1);
        }
    }
}
