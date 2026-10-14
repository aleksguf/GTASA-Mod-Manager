package com.gtasa.modmanager;

import android.app.*;
import android.os.*;
import android.content.*;
import android.net.Uri;
import android.view.*;
import android.widget.*;

public class MainActivity extends Activity {
    TextView info;
    Uri folder, archive;

    public void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(1);
        l.setPadding(24,24,24,24);

        TextView title = new TextView(this);
        title.setText("GTA SA Mod Manager");
        title.setTextSize(24);
        l.addView(title);

        info = new TextView(this);
        info.setText("GTA San Andreas Android 2.00");
        l.addView(info);

        add(l,"Выбрать папку игры",1);
        add(l,"Выбрать ZIP с модом",2);
        add(l,"Проверить выбранные файлы",3);

        TextView note = new TextView(this);
        note.setText("\nMVP 0.1 — сначала тестируй на копии игры. Автоматическая установка и откат пока не реализованы.");
        l.addView(note);

        setContentView(l);
    }

    void add(LinearLayout l,String text,int action) {
        Button b = new Button(this);
        b.setText(text);
        b.setOnClickListener(v -> {
            if(action==1 || action==2) {
                Intent i = new Intent(action==1 ?
                    Intent.ACTION_OPEN_DOCUMENT_TREE :
                    Intent.ACTION_OPEN_DOCUMENT);
                if(action==2) {
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("application/zip");
                }
                startActivityForResult(i,action);
            } else {
                info.setText("Папка: "+(folder==null?"не выбрана":"выбрана")+
                    "\nАрхив: "+(archive==null?"не выбран":"выбран"));
            }
        });
        l.addView(b);
    }

    protected void onActivityResult(int r,int c,Intent d) {
        super.onActivityResult(r,c,d);
        if(c!=RESULT_OK || d==null) return;
        if(r==1) folder=d.getData();
        if(r==2) archive=d.getData();
        info.setText("Выбор сохранён. Нажми «Проверить выбранные файлы».");
    }
}
