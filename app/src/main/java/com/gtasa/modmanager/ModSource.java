package com.gtasa.modmanager;

import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.DocumentsContract.Document;

import java.io.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Where mod files come from. Everything is streamed file by file, nothing is loaded into
 * memory or unpacked to a temp folder, so archive size is limited only by free space.
 */
abstract class ModSource {
    interface Visitor {
        /** in must not be closed by the visitor. */
        void file(String path, long size, InputStream in) throws IOException;
    }

    final ContentResolver cr;
    final Uri uri;
    volatile long total, done;

    ModSource(ContentResolver cr, Uri uri) {
        this.cr = cr;
        this.uri = uri;
    }

    abstract void forEach(Visitor v) throws IOException;

    /** Wraps in so that every byte read is added to done (drives the progress bar). */
    InputStream count(InputStream in) {
        return new FilterInputStream(in) {
            public int read() throws IOException {
                int r = super.read();
                if (r >= 0) done++;
                return r;
            }
            public int read(byte[] b, int off, int len) throws IOException {
                int r = super.read(b, off, len);
                if (r > 0) done += r;
                return r;
            }
            public long skip(long n) throws IOException {
                long r = super.skip(n);
                done += r;
                return r;
            }
        };
    }

    /** ZIP archive, including ZIP64 (files and archives larger than 4 GB). */
    static class Zip extends ModSource {
        Zip(ContentResolver cr, Uri uri, long size) {
            super(cr, uri);
            total = size;
        }

        void forEach(Visitor v) throws IOException {
            InputStream raw = cr.openInputStream(uri);
            if (raw == null) throw new FileNotFoundException("Не удалось открыть архив");
            try (ZipInputStream zin = new ZipInputStream(count(new BufferedInputStream(raw, 1 << 20)))) {
                ZipEntry e;
                while ((e = zin.getNextEntry()) != null) {
                    if (!e.isDirectory()) v.file(e.getName(), e.getSize(), zin);
                    zin.closeEntry();
                }
            }
        }
    }

    /** Already unpacked mod folder: the most reliable way for very large mods. */
    static class Folder extends ModSource {
        Folder(ContentResolver cr, Uri tree) {
            super(cr, tree);
        }

        void forEach(Visitor v) throws IOException {
            String root = DocumentsContract.getTreeDocumentId(uri);
            total = sizeOf(root);
            walk(root, "", v);
        }

        private Cursor children(String docId) {
            return cr.query(DocumentsContract.buildChildDocumentsUriUsingTree(uri, docId),
                    new String[]{Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
                            Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE}, null, null, null);
        }

        private long sizeOf(String docId) {
            long s = 0;
            try (Cursor c = children(docId)) {
                while (c != null && c.moveToNext())
                    s += Document.MIME_TYPE_DIR.equals(c.getString(2)) ? sizeOf(c.getString(0))
                            : c.isNull(3) ? 0 : c.getLong(3);
            }
            return s;
        }

        private void walk(String docId, String prefix, Visitor v) throws IOException {
            try (Cursor c = children(docId)) {
                while (c != null && c.moveToNext()) {
                    String id = c.getString(0), path = prefix + c.getString(1);
                    if (Document.MIME_TYPE_DIR.equals(c.getString(2))) {
                        walk(id, path + "/", v);
                        continue;
                    }
                    long size = c.isNull(3) ? -1 : c.getLong(3);
                    try (InputStream in = cr.openInputStream(
                            DocumentsContract.buildDocumentUriUsingTree(uri, id))) {
                        if (in == null) throw new FileNotFoundException(path);
                        long before = done;
                        v.file(path, size, count(in));
                        done = before + Math.max(size, done - before);
                    }
                }
            }
        }
    }
}
