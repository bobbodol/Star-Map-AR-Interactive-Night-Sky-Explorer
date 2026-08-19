# StarMap.java
/**
 * 🌟 Star Map AR – Interactive Night Sky Explorer (Java Edition)
 * Features: ASCII sky map, constellation tracing, star search, favourites, simulation
 * Requires: Java 17+
 */

import java.io.*;
import java.nio.file.*;
import java.time.*;
import java.time.format.*;
import java.util.*;
import java.util.regex.*;

public class StarMap {
    // ─── Colors ────────────────────────────────────────────────────────────

    private static final String RESET = "\u001B[0m";
    private static final String BRIGHT = "\u001B[1m";
    private static final String DIM = "\u001B[2m";
    private static final String RED = "\u001B[31m";
    private static final String GREEN = "\u001B[32m";
    private static final String YELLOW = "\u001B[33m";
    private static final String BLUE = "\u001B[34m";
    private static final String MAGENTA = "\u001B[35m";
    private static final String CYAN = "\u001B[36m";
    private static final String WHITE = "\u001B[37m";

    private static String c(String text, String color) { return color + text + RESET; }

    // ─── Star Class ──────────────────────────────────────────────────────

    static class Star {
        String name;
        double ra;    // hours
        double dec;   // degrees
        double mag;
        String constel;

        Star(String name, double ra, double dec, double mag, String constel) {
            this.name = name; this.ra = ra; this.dec = dec; this.mag = mag; this.constel = constel;
        }
    }

    // ─── Database ─────────────────────────────────────────────────────────

    private static final List<Star> STARS = Arrays.asList(
        // ... (full list)
    );

    // ─── User Data ─────────────────────────────────────────────────────────

    static class UserData {
        List<String> favourites = new ArrayList<>();
        double latitude = 40.7;
        double longitude = -74.0;
        int timezone = -5;
    }

    // ─── Config ────────────────────────────────────────────────────────────

    private static final String DATA_DIR = System.getProperty("user.home") + "/.star_map";
    private static final String DATA_FILE = DATA_DIR + "/user.json";

    // ─── Sky Map Engine ──────────────────────────────────────────────────

    static class SkyMap {
        private double latRad, lonRad;
        private int timezone;
        private LocalDateTime now;
        private List<Star> stars;

        SkyMap(double lat, double lon, int tz) {
            this.latRad = Math.toRadians(lat);
            this.lonRad = Math.toRadians(lon);
            this.timezone = tz;
            this.now = LocalDateTime.now();
            this.stars = STARS;
        }

        void setTime(LocalDateTime dt) { this.now = dt; }

        private double julianDate(LocalDateTime dt) {
            int year = dt.getYear();
            int month = dt.getMonthValue();
            double day = dt.getDayOfMonth() + dt.getHour() / 
