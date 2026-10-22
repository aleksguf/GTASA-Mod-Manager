package com.gtasa.modmanager;

import android.content.ContentResolver;
import android.net.Uri;
import android.os.StatFs;

import java.io.*;
import java.util.*;

/**
 * Installs a mod into the game folder and removes it again.
 *
 * Any file type can be replaced or added: textures, models, data, scripts, audio of any
 * format (SFX, STREAMS, radio, .osw/.wav/.mp3/.ogg...), cutscenes (anim/cuts.img and their
 * audio) and so on. The file goes wherever the same file already lies in the game folder;
 * new files are put into an existing top-level game folder named in the archive path.
 */
class ModInstaller {
    interface Progress {
        void update(String text, long done, long total);
    }

    static class Report {
        int replaced, added;
        final List<String> skipped = new ArrayList<>();
    }

    static final long SPACE_RESERVE = 64L << 20;
    static final Set<String> JUNK = new HashSet<>(Arrays.asList(
            "__macosx", ".ds_store", "thumbs.db", "desktop.ini"));

    final ContentResolver cr;
    final ModStore store;
    final Progress progress;
    final byte[] buf = new byte[1 << 20];

    ModInstaller(ContentResolver cr, ModStore store, Progress progress) {
        this.cr = cr;
        this.store = store;
        this.progress = progress;
    }

    GameTree scan(Uri game) throws IOException {
        progress.update("Сканирую папку игры…", 0, 0);
        GameTree t = new GameTree(cr, game);
        if (t.fileCount() == 0) throw new IOException("Папка игры пуста или нет доступа к ней");
        return t;
    }

    Report install(Uri game, ModSource src, String name) throws IOException {
        GameTree t = scan(game);
        ModStore.Mod m = store.begin(name);
        Report r = new Report();
        try {
            src.forEach((path, size, in) -> {
                progress.update(path, src.done, src.total);
                String[] segs = split(path);
                if (segs == null) return;
                String target = resolve(t, segs);
                GameTree.Node node = target == null ? null : t.get(target);
                if (target == null || node != null && node.dir) {
                    r.skipped.add(String.join("/", segs));
                    return;
                }
                if (m.find(target) == null) {
                    if (node != null) backup(t, node, m.backup(node.path));
                    m.record(node != null ? node.path : target, node != null);
                    if (node != null) r.replaced++;
                    else r.added++;
                }
                if (node == null) node = t.createFile(target);
                try (OutputStream out = cr.openOutputStream(t.uri(node), "wt")) {
                    if (out == null) throw new FileNotFoundException(node.path);
                    copy(in, out, path, src);
                }
            });
            if (m.files.isEmpty()) store.drop(m);
            else store.commit(m);
            return r;
        } catch (IOException | RuntimeException e) {
            progress.update("Ошибка, откатываю изменения…", 0, 0);
            try {
                uninstall(t, m);
            } catch (Exception e2) {
                e.addSuppressed(e2);
            }
            throw e;
        }
    }

    void uninstall(Uri game, ModStore.Mod m) throws IOException {
        uninstall(scan(game), m);
    }

    /**
     * Puts back what the files looked like before m. If a later mod changed the same file,
     * the file stays as that mod left it, and m's backup becomes that mod's backup instead.
     */
    private void uninstall(GameTree t, ModStore.Mod m) throws IOException {
        m.close();
        Set<ModStore.Mod> changed = new HashSet<>();
        int i = 0, n = m.files.size();
        for (Map.Entry<String, Boolean> e : m.files.entrySet()) {
            String path = e.getKey();
            boolean existed = e.getValue();
            progress.update("Восстанавливаю " + path, i++, n);
            File b = m.backup(path);
            ModStore.Mod next = store.nextOwner(m, path);
            if (next != null) {
                String np = next.find(path);
                File nb = next.backup(np);
                nb.delete();
                if (existed) {
                    nb.getParentFile().mkdirs();
                    if (!b.renameTo(nb)) copyFile(b, nb);
                }
                next.put(np, existed);
                changed.add(next);
                continue;
            }
            GameTree.Node node = t.get(path);
            if (existed) {
                if (!b.isFile()) throw new FileNotFoundException("Нет резервной копии: " + path);
                if (node == null) node = t.createFile(path);
                try (InputStream in = new FileInputStream(b);
                     OutputStream out = cr.openOutputStream(t.uri(node), "wt")) {
                    if (out == null) throw new FileNotFoundException(path);
                    copy(in, out, null, null);
                }
            } else if (node != null && !node.dir) {
                t.delete(node);
            }
        }
        for (ModStore.Mod c : changed) c.rewriteJournal();
        store.drop(m);
    }

    /** Archive path -> clean segments, or null for junk and unsafe paths. */
    static String[] split(String path) {
        List<String> l = new ArrayList<>();
        for (String s : path.replace('\\', '/').split("/")) {
            if (s.isEmpty() || s.equals(".")) continue;
            if (s.equals("..") || JUNK.contains(GameTree.key(s))) return null;
            l.add(s);
        }
        return l.isEmpty() ? null : l.toArray(new String[0]);
    }

    /** Where a mod file goes in the game folder (real letter case), or null if unknown. */
    static String resolve(GameTree t, String[] segs) {
        int n = segs.length;
        // 1. Same relative path exists: "files/audio/SFX/GENRL.osw", "audio/SFX/GENRL.osw", ...
        for (int i = 0; i < n; i++) {
            GameTree.Node f = t.get(join(segs, i));
            if (f != null && !f.dir) return f.path;
        }
        // 2. File with this name exists exactly once (or once inside a folder with the same name)
        List<GameTree.Node> same = t.byName.get(GameTree.key(segs[n - 1]));
        if (same != null && same.size() == 1) return same.get(0).path;
        if (same != null && n > 1) {
            GameTree.Node pick = null;
            for (GameTree.Node c : same)
                if (GameTree.name(GameTree.parent(c.path)).equalsIgnoreCase(segs[n - 2])) {
                    if (pick != null) return null;
                    pick = c;
                }
            if (pick != null) return pick.path;
        }
        // 3. New file: keep the path from the first folder that exists in the game root
        for (int i = 0; i < n - 1; i++) {
            GameTree.Node d = t.get(segs[i]);
            if (d != null && d.dir) return d.path + "/" + join(segs, i + 1);
        }
        return null;
    }

    static String join(String[] segs, int from) {
        return String.join("/", Arrays.asList(segs).subList(from, segs.length));
    }

    private void backup(GameTree t, GameTree.Node node, File to) throws IOException {
        long free = new StatFs(store.root.getPath()).getAvailableBytes();
        if (free < node.size + SPACE_RESERVE)
            throw new IOException("Недостаточно места для резервной копии " + node.path
                    + ": нужно " + mb(node.size + SPACE_RESERVE) + ", свободно " + mb(free));
        to.getParentFile().mkdirs();
        try (InputStream in = cr.openInputStream(t.uri(node));
             OutputStream out = new FileOutputStream(to)) {
            if (in == null) throw new FileNotFoundException(node.path);
            copy(in, out, "Резервная копия " + node.path, null);
        }
    }

    private void copyFile(File from, File to) throws IOException {
        try (InputStream in = new FileInputStream(from); OutputStream out = new FileOutputStream(to)) {
            copy(in, out, null, null);
        }
    }

    private void copy(InputStream in, OutputStream out, String label, ModSource src) throws IOException {
        int r;
        while ((r = in.read(buf)) > 0) {
            out.write(buf, 0, r);
            if (label != null) progress.update(label, src == null ? 0 : src.done, src == null ? 0 : src.total);
        }
    }

    static String mb(long bytes) {
        return bytes >= 1L << 30 ? String.format(Locale.ROOT, "%.2f ГБ", bytes / (double) (1L << 30))
                : (bytes >> 20) + " МБ";
    }
}
