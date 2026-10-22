package com.gtasa.modmanager;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Installed mods in install order plus a backup of every file each mod touched.
 *
 * backups/state.json            list of mods (oldest first)
 * backups/<id>/journal.tsv      "existed\tpath" per touched file, appended before the file is written
 * backups/<id>/files/<path>     content of the file right before this mod overwrote it
 */
class ModStore {
    static class Mod {
        String id, name;
        long time;
        boolean complete;
        File dir;
        /** path in game folder -> did the file exist before this mod */
        final LinkedHashMap<String, Boolean> files = new LinkedHashMap<>();
        /** lower-case path -> path as stored in files */
        final Map<String, String> keys = new HashMap<>();
        Writer journal;

        File backup(String path) { return new File(dir, "files/" + path); }

        String find(String path) { return keys.get(GameTree.key(path)); }

        void put(String path, boolean existed) {
            files.put(path, existed);
            keys.put(GameTree.key(path), path);
        }

        /** Must be called before the game file is changed, so a crash can still be rolled back. */
        void record(String path, boolean existed) throws IOException {
            put(path, existed);
            if (journal == null)
                journal = new OutputStreamWriter(new FileOutputStream(new File(dir, "journal.tsv"), true),
                        StandardCharsets.UTF_8);
            journal.write((existed ? "1\t" : "0\t") + path + "\n");
            journal.flush();
        }

        void close() {
            try { if (journal != null) journal.close(); } catch (IOException ignored) {}
            journal = null;
        }

        void rewriteJournal() throws IOException {
            close();
            try (Writer w = new OutputStreamWriter(new FileOutputStream(new File(dir, "journal.tsv")),
                    StandardCharsets.UTF_8)) {
                for (Map.Entry<String, Boolean> e : files.entrySet())
                    w.write((e.getValue() ? "1\t" : "0\t") + e.getKey() + "\n");
            }
        }
    }

    final File root;
    final List<Mod> mods = new ArrayList<>();

    ModStore(File root) {
        this.root = root;
        root.mkdirs();
        try {
            JSONArray a = new JSONObject(read(new File(root, "state.json"))).getJSONArray("mods");
            for (int i = 0; i < a.length(); i++) {
                JSONObject o = a.getJSONObject(i);
                Mod m = new Mod();
                m.id = o.getString("id");
                m.name = o.getString("name");
                m.time = o.optLong("time");
                m.complete = o.optBoolean("complete");
                m.dir = new File(root, m.id);
                loadJournal(m);
                mods.add(m);
            }
        } catch (IOException | JSONException ignored) {
            // no state yet
        }
    }

    private static String read(File f) throws IOException {
        try (InputStream in = new FileInputStream(f)) {
            ByteArrayOutputStream o = new ByteArrayOutputStream();
            byte[] b = new byte[8192];
            int r;
            while ((r = in.read(b)) > 0) o.write(b, 0, r);
            return o.toString("UTF-8");
        }
    }

    private static void loadJournal(Mod m) {
        try (BufferedReader r = new BufferedReader(new InputStreamReader(
                new FileInputStream(new File(m.dir, "journal.tsv")), StandardCharsets.UTF_8))) {
            String l;
            while ((l = r.readLine()) != null)
                if (l.length() > 2) m.put(l.substring(2), l.charAt(0) == '1');
        } catch (IOException ignored) {
        }
    }

    void save() throws IOException {
        JSONArray a = new JSONArray();
        try {
            for (Mod m : mods)
                a.put(new JSONObject().put("id", m.id).put("name", m.name)
                        .put("time", m.time).put("complete", m.complete));
            File tmp = new File(root, "state.json.tmp");
            try (Writer w = new OutputStreamWriter(new FileOutputStream(tmp), StandardCharsets.UTF_8)) {
                w.write(new JSONObject().put("mods", a).toString(1));
            }
            if (!tmp.renameTo(new File(root, "state.json"))) throw new IOException("state.json");
        } catch (JSONException e) {
            throw new IOException(e);
        }
    }

    Mod begin(String name) throws IOException {
        Mod m = new Mod();
        m.time = System.currentTimeMillis();
        m.id = Long.toString(m.time, 36);
        m.name = name;
        m.dir = new File(root, m.id);
        if (!m.dir.mkdirs()) throw new IOException("Не удалось создать папку бэкапа");
        mods.add(m);
        save();
        return m;
    }

    void commit(Mod m) throws IOException {
        m.close();
        m.complete = true;
        save();
    }

    /** Mods installed after m that also changed path, oldest first. */
    Mod nextOwner(Mod m, String path) {
        for (int i = mods.indexOf(m) + 1; i < mods.size(); i++)
            if (mods.get(i).find(path) != null) return mods.get(i);
        return null;
    }

    void drop(Mod m) throws IOException {
        m.close();
        deleteTree(m.dir);
        mods.remove(m);
        save();
    }

    static void deleteTree(File f) {
        File[] c = f.listFiles();
        if (c != null) for (File x : c) deleteTree(x);
        f.delete();
    }
}
