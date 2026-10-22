package com.gtasa.modmanager;

import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.DocumentsContract.Document;

import java.io.FileNotFoundException;
import java.util.*;

/** Index of the game folder (SAF tree): every file and folder by relative path and by name. */
class GameTree {
    static class Node {
        String path, docId;
        boolean dir;
        long size;
    }

    final ContentResolver cr;
    final Uri tree;
    final Map<String, Node> byPath = new HashMap<>();
    final Map<String, List<Node>> byName = new HashMap<>();

    GameTree(ContentResolver cr, Uri tree) {
        this.cr = cr;
        this.tree = tree;
        Node root = new Node();
        root.path = "";
        root.docId = DocumentsContract.getTreeDocumentId(tree);
        root.dir = true;
        byPath.put("", root);
        scan(root);
    }

    static String key(String path) { return path.toLowerCase(Locale.ROOT); }

    static String name(String path) { return path.substring(path.lastIndexOf('/') + 1); }

    static String parent(String path) {
        int i = path.lastIndexOf('/');
        return i < 0 ? "" : path.substring(0, i);
    }

    Node get(String path) { return byPath.get(key(path)); }

    Uri uri(Node n) { return DocumentsContract.buildDocumentUriUsingTree(tree, n.docId); }

    int fileCount() {
        int c = 0;
        for (Node n : byPath.values()) if (!n.dir) c++;
        return c;
    }

    private void scan(Node dir) {
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, dir.docId);
        List<Node> subdirs = new ArrayList<>();
        try (Cursor c = cr.query(children, new String[]{
                Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
                Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE}, null, null, null)) {
            if (c == null) return;
            while (c.moveToNext()) {
                Node n = new Node();
                n.docId = c.getString(0);
                n.path = dir.path.isEmpty() ? c.getString(1) : dir.path + "/" + c.getString(1);
                n.dir = Document.MIME_TYPE_DIR.equals(c.getString(2));
                n.size = c.isNull(3) ? 0 : c.getLong(3);
                add(n);
                if (n.dir) subdirs.add(n);
            }
        }
        for (Node d : subdirs) scan(d);
    }

    private void add(Node n) {
        byPath.put(key(n.path), n);
        if (!n.dir) byName.computeIfAbsent(key(name(n.path)), k -> new ArrayList<>()).add(n);
    }

    void remove(Node n) {
        byPath.remove(key(n.path));
        List<Node> l = byName.get(key(name(n.path)));
        if (l != null) l.remove(n);
    }

    /** Returns the folder, creating missing parts. Existing folders keep their real letter case. */
    Node ensureDir(String path) throws FileNotFoundException {
        Node n = get(path);
        if (n != null) {
            if (!n.dir) throw new FileNotFoundException("Не папка: " + n.path);
            return n;
        }
        Node p = ensureDir(parent(path));
        return create(p, name(path), true);
    }

    /** Creates an empty file at path (its folders are created as needed). */
    Node createFile(String path) throws FileNotFoundException {
        return create(ensureDir(parent(path)), name(path), false);
    }

    private Node create(Node parent, String name, boolean dir) throws FileNotFoundException {
        // octet-stream keeps any extension (.osw, .img, .txd, .wav, ...) exactly as given
        Uri u = DocumentsContract.createDocument(cr, uri(parent),
                dir ? Document.MIME_TYPE_DIR : "application/octet-stream", name);
        if (u == null) throw new FileNotFoundException("Не удалось создать " + parent.path + "/" + name);
        Node n = new Node();
        n.docId = DocumentsContract.getDocumentId(u);
        n.path = parent.path.isEmpty() ? name : parent.path + "/" + name;
        n.dir = dir;
        add(n);
        return n;
    }

    void delete(Node n) throws FileNotFoundException {
        DocumentsContract.deleteDocument(cr, uri(n));
        remove(n);
    }
}
