package com.gtasa.modmanager;

import android.app.*;
import android.os.*;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;

import java.text.DateFormat;
import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipException;

public class MainActivity extends Activity {
    static final int PICK_GAME = 1, PICK_ZIP = 2, PICK_FOLDER = 3;
    static final Uri GTASA_FILES = Uri.parse("content://com.android.externalstorage.documents/document/"
            + "primary%3AAndroid%2Fdata%2Fcom.rockstargames.gtasa%2Ffiles");

    TextView info, status;
    ProgressBar bar;
    LinearLayout modList;
    final List<Button> buttons = new ArrayList<>();
    Uri game;
    ModStore store;
    final ExecutorService worker = Executors.newSingleThreadExecutor();
    boolean busy;
    long lastUi;

    public void onCreate(Bundle b) {
        super.onCreate(b);
        store = new ModStore(new java.io.File(getExternalFilesDir(null), "backups"));
        String saved = getPreferences(MODE_PRIVATE).getString("game", null);
        if (saved != null) game = Uri.parse(saved);

        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(24, 24, 24, 24);

        TextView title = new TextView(this);
        title.setText("GTA SA Mod Manager");
        title.setTextSize(24);
        l.addView(title);

        info = new TextView(this);
        l.addView(info);

        add(l, "Выбрать папку игры", PICK_GAME);
        add(l, "Установить мод из ZIP", PICK_ZIP);
        add(l, "Установить мод из папки (распакованный)", PICK_FOLDER);

        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(1000);
        bar.setVisibility(View.GONE);
        l.addView(bar);

        status = new TextView(this);
        status.setPadding(0, 12, 0, 12);
        status.setTextIsSelectable(true);
        l.addView(status);

        TextView header = new TextView(this);
        header.setText("Установленные моды (сверху — последний):");
        header.setTextSize(18);
        l.addView(header);
        modList = new LinearLayout(this);
        modList.setOrientation(LinearLayout.VERTICAL);
        l.addView(modList);

        TextView note = new TextView(this);
        note.setText("\nЗаменяются любые файлы игры: текстуры, модели, data, скрипты, звук любого"
                + " формата (SFX, STREAMS, радио), катсцены и т.д. Размер мода не ограничен — архив"
                + " читается потоком, ZIP64 (больше 4 ГБ) поддерживается. Несколько модов можно ставить"
                + " поверх друг друга и удалять в любом порядке.\n\nПеред заменой оригиналы сохраняются"
                + " в Android/data/com.gtasa.modmanager/files/backups — нужно свободное место примерно"
                + " равное размеру заменяемых файлов. При удалении приложения бэкапы удаляются.\n\n"
                + "Если ZIP не открывается (Deflate64, 7z, RAR) — распакуй мод и выбери папку."
                + " Папка игры: Android/data/com.rockstargames.gtasa/files.");
        l.addView(note);

        ScrollView sv = new ScrollView(this);
        sv.addView(l);
        setContentView(sv);
        refresh();
    }

    void add(LinearLayout l, String text, int action) {
        Button b = new Button(this);
        b.setText(text);
        b.setOnClickListener(v -> {
            if (action != PICK_GAME && game == null) {
                status.setText("Сначала выбери папку игры.");
                return;
            }
            Intent i;
            if (action == PICK_ZIP) {
                i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                i.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{
                        "application/zip", "application/x-zip-compressed", "application/octet-stream"});
            } else {
                i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
                if (action == PICK_GAME) {
                    i.putExtra(DocumentsContract.EXTRA_INITIAL_URI, GTASA_FILES);
                    i.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                            | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                }
            }
            startActivityForResult(i, action);
        });
        buttons.add(b);
        l.addView(b);
    }

    protected void onActivityResult(int r, int c, Intent d) {
        super.onActivityResult(r, c, d);
        if (c != RESULT_OK || d == null || d.getData() == null) return;
        Uri u = d.getData();
        if (r == PICK_GAME) {
            try {
                getContentResolver().takePersistableUriPermission(u,
                        Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            } catch (SecurityException ignored) {
                // still usable until the app is closed
            }
            game = u;
            getPreferences(MODE_PRIVATE).edit().putString("game", u.toString()).apply();
            status.setText("Папка игры выбрана.");
            refresh();
        } else if (r == PICK_ZIP) {
            install(new ModSource.Zip(getContentResolver(), u, size(u)), name(u));
        } else if (r == PICK_FOLDER) {
            install(new ModSource.Folder(getContentResolver(), u), name(
                    DocumentsContract.buildDocumentUriUsingTree(u, DocumentsContract.getTreeDocumentId(u))));
        }
    }

    void install(ModSource src, String name) {
        Uri g = game;
        run("Установка «" + name + "»", inst -> {
            ModInstaller.Report rep = inst.install(g, src, name);
            StringBuilder s = new StringBuilder();
            if (rep.replaced + rep.added == 0) s.append("Ничего не установлено: ни один файл мода не подошёл к папке игры.");
            else s.append("Готово: «").append(name).append("»\nЗаменено файлов: ").append(rep.replaced)
                    .append("\nДобавлено новых: ").append(rep.added);
            if (!rep.skipped.isEmpty()) {
                s.append("\n\nПропущено ").append(rep.skipped.size()).append(" (не нашёл, куда положить):");
                for (int i = 0; i < rep.skipped.size() && i < 30; i++) s.append("\n• ").append(rep.skipped.get(i));
                if (rep.skipped.size() > 30) s.append("\n…");
            }
            return s.toString();
        });
    }

    void uninstall(List<ModStore.Mod> mods) {
        Uri g = game;
        run("Удаление", inst -> {
            for (ModStore.Mod m : mods) inst.uninstall(g, m);
            return mods.size() == 1 ? "Мод «" + mods.get(0).name + "» удалён, файлы восстановлены."
                    : "Все моды удалены, оригинальные файлы восстановлены.";
        });
    }

    interface Job {
        String run(ModInstaller inst) throws Exception;
    }

    void run(String what, Job job) {
        setBusy(true);
        status.setText(what + "…");
        ModInstaller inst = new ModInstaller(getContentResolver(), store, (text, done, total) -> {
            long now = SystemClock.uptimeMillis();
            if (now - lastUi < 150) return;
            lastUi = now;
            runOnUiThread(() -> {
                bar.setIndeterminate(total <= 0);
                if (total > 0) bar.setProgress((int) (done * 1000 / total));
                status.setText(what + "\n" + (total > 0 && done <= total && total > 1000
                        ? ModInstaller.mb(done) + " / " + ModInstaller.mb(total) + "\n" : "") + text);
            });
        });
        worker.execute(() -> {
            String msg;
            try {
                msg = job.run(inst);
            } catch (ZipException e) {
                msg = "Ошибка архива: " + e.getMessage() + "\nВозможно, это не ZIP или он сжат Deflate64."
                        + " Распакуй мод и выбери «Установить мод из папки». Изменения отменены.";
            } catch (Exception e) {
                msg = "Ошибка: " + e + "\nНезавершённая установка откатывается автоматически.";
            }
            String result = msg;
            runOnUiThread(() -> {
                setBusy(false);
                status.setText(result);
                refresh();
            });
        });
    }

    void setBusy(boolean b) {
        busy = b;
        for (Button x : buttons) x.setEnabled(!b);
        bar.setVisibility(b ? View.VISIBLE : View.GONE);
        bar.setIndeterminate(true);
        if (b) getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    void refresh() {
        info.setText("Папка игры: " + (game == null ? "не выбрана" : Uri.decode(game.getLastPathSegment())));
        modList.removeAllViews();
        DateFormat df = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT);
        for (int i = store.mods.size() - 1; i >= 0; i--) {
            ModStore.Mod m = store.mods.get(i);
            LinearLayout row = new LinearLayout(this);
            row.setGravity(Gravity.CENTER_VERTICAL);
            TextView t = new TextView(this);
            t.setText(m.name + (m.complete ? "" : " (не завершена)") + "\n" + df.format(new Date(m.time))
                    + " · файлов: " + m.files.size());
            row.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            Button del = new Button(this);
            del.setText("Удалить");
            del.setOnClickListener(v -> confirm("Удалить «" + m.name + "» и вернуть файлы?",
                    () -> uninstall(Collections.singletonList(m))));
            del.setEnabled(!busy && game != null);
            row.addView(del);
            modList.addView(row);
        }
        if (store.mods.isEmpty()) {
            TextView t = new TextView(this);
            t.setText("нет");
            modList.addView(t);
        } else {
            Button all = new Button(this);
            all.setText("Удалить все моды (вернуть оригинал)");
            all.setEnabled(!busy && game != null);
            all.setOnClickListener(v -> confirm("Удалить все моды и вернуть оригинальные файлы?", () -> {
                List<ModStore.Mod> l = new ArrayList<>(store.mods);
                Collections.reverse(l);
                uninstall(l);
            }));
            modList.addView(all);
        }
    }

    void confirm(String q, Runnable yes) {
        if (busy) return;
        new AlertDialog.Builder(this).setMessage(q)
                .setPositiveButton("Да", (d, w) -> yes.run())
                .setNegativeButton("Отмена", null).show();
    }

    Cursor query(Uri u, String col) {
        return getContentResolver().query(u, new String[]{col}, null, null, null);
    }

    String name(Uri u) {
        try (Cursor c = query(u, OpenableColumns.DISPLAY_NAME)) {
            if (c != null && c.moveToFirst() && !c.isNull(0)) return c.getString(0);
        } catch (Exception ignored) {
        }
        return u.getLastPathSegment();
    }

    long size(Uri u) {
        try (Cursor c = query(u, OpenableColumns.SIZE)) {
            if (c != null && c.moveToFirst() && !c.isNull(0)) return c.getLong(0);
        } catch (Exception ignored) {
        }
        return 0;
    }
}
