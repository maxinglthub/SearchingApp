import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from typing import Dict, Optional

# 匯入資料核心
try:
    from searching_main import ClientDB
except ImportError:
    print("錯誤：找不到 searching_main.py 檔案。")
    sys.exit(1)

# 設定 CustomTkinter 外觀
ctk.set_appearance_mode("Dark")  # 模式: "System" (標準), "Dark", "Light"
ctk.set_default_color_theme("blue")  # 主題顏色: "blue", "green", "dark-blue"

class ClientApp(ctk.CTk):
    def __init__(self, file_path):
        super().__init__()
        self.title("廷好搜客戶資料管理系統 (CustomTkinter版)")
        self.geometry("1100x750")

        # 1. 載入資料庫
        self.file_path = file_path
        try:
            self.db = ClientDB(file_path)
        except Exception as e:
            messagebox.showerror("載入錯誤", f"無法載入檔案：{e}")
            self.destroy()
            return

        # 2. 設定 Grid 佈局權重
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 3. 建立介面元件
        self.create_top_panel()
        self.create_treeview_panel()

        # 4. 載入初始資料
        self.load_data_to_treeview(self.db.df)

    def create_top_panel(self):
        """建立頂部操作區"""
        # 使用 CTkFrame
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        self.top_frame.grid_columnconfigure(1, weight=1) # 讓搜尋框伸縮

        # 搜尋標籤
        ctk.CTkLabel(self.top_frame, text="搜尋:", font=("Microsoft JhengHei UI", 14)).grid(row=0, column=0, padx=10, pady=10)

        # 搜尋輸入框
        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="輸入姓名、電話或編號...", width=200)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        self.search_entry.bind("<Return>", lambda event: self.run_search()) # 按 Enter 搜尋

        # 按鈕群組 (使用不同顏色區分)
        ctk.CTkButton(self.top_frame, text="搜尋", width=80, command=self.run_search).grid(row=0, column=2, padx=5)
        
        ctk.CTkButton(self.top_frame, text="重置", width=80, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), 
                      command=self.run_reset).grid(row=0, column=3, padx=5)

        # 分隔線概念 (透過 padding)
        ctk.CTkButton(self.top_frame, text="新增", width=80, fg_color="#2CC985", hover_color="#229A65", text_color="white",
                      command=lambda: self.open_add_edit_window()).grid(row=0, column=4, padx=(20, 5))

        ctk.CTkButton(self.top_frame, text="刪除", width=80, fg_color="#C0392B", hover_color="#922B21", 
                      command=self.run_delete).grid(row=0, column=5, padx=5)

        ctk.CTkButton(self.top_frame, text="存檔", width=80, command=self.run_save).grid(row=0, column=6, padx=(5, 15))

        # 資料筆數
        self.count_label = ctk.CTkLabel(self.top_frame, text=f"筆數: {len(self.db.df)}")
        self.count_label.grid(row=0, column=7, padx=15)

    def create_treeview_panel(self):
        """建立表格區域 (CTk 沒有內建表格，需使用 ttk.Treeview 並美化)"""
        self.tree_frame = ctk.CTkFrame(self, corner_radius=10)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # --- 自訂 Treeview 樣式 (讓它看起來像 CTk 風格) ---
        style = ttk.Style()
        style.theme_use("default") # 重置為預設以便自訂
        
        # 設定顏色變數
        bg_color = self.cget("fg_color")[1] if isinstance(self.cget("fg_color"), tuple) else "#2b2b2b"
        field_bg = "#2b2b2b" # 表格背景色 (深灰)
        text_color = "white"
        selected_bg = "#1f538d" # CTk 預設藍色

        style.configure("Treeview", 
                        background=field_bg, 
                        foreground=text_color, 
                        fieldbackground=field_bg,
                        borderwidth=0,
                        rowheight=30,
                        font=("Microsoft JhengHei UI", 11))
        
        style.map('Treeview', background=[('selected', selected_bg)])

        style.configure("Treeview.Heading", 
                        background="#3a3d3e", 
                        foreground="white", 
                        relief="flat",
                        font=("Microsoft JhengHei UI", 11, "bold"))
        
        style.map("Treeview.Heading",
                  background=[('active', '#4a4d4e')])

        # 建立 Scrollbar (使用 CTk 的滾動條比較漂亮)
        self.tree_scroll_y = ctk.CTkScrollbar(self.tree_frame, orientation="vertical")
        self.tree_scroll_y.grid(row=0, column=1, sticky="ns", padx=(0,5), pady=5)
        
        self.tree_scroll_x = ctk.CTkScrollbar(self.tree_frame, orientation="horizontal")
        self.tree_scroll_x.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,5))

        # 建立 Treeview
        self.tree = ttk.Treeview(self.tree_frame, show="headings", 
                                 yscrollcommand=self.tree_scroll_y.set, 
                                 xscrollcommand=self.tree_scroll_x.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 連結 Scrollbar
        self.tree_scroll_y.configure(command=self.tree.yview)
        self.tree_scroll_x.configure(command=self.tree.xview)

        # 雙擊事件
        self.tree.bind("<Double-1>", self.open_edit_window)

    def load_data_to_treeview(self, df):
        columns = [c for c in self.db.display_cols if c in df.columns]
        self.tree["columns"] = columns
        self.tree.delete(*self.tree.get_children())

        for col in columns:
            self.tree.heading(col, text=col)
            # 根據欄位名稱設定寬度
            if col in ["備註", "地址"]:
                self.tree.column(col, width=250, anchor="w")
            elif col in ["電話", "手機", "客戶編號"]:
                self.tree.column(col, width=120, anchor="center")
            else:
                self.tree.column(col, width=100, anchor="center")

        for index, row in df.iterrows():
            values = [row[col] for col in columns]
            self.tree.insert("", "end", iid=index, values=values)
        
        self.count_label.configure(text=f"筆數: {len(df)}")

    def run_search(self):
        query = self.search_entry.get().strip()
        q_words = query.split()
        try:
            results = self.db.search(q_words)
            self.load_data_to_treeview(results)
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def run_reset(self):
        self.search_entry.delete(0, "end")
        self.load_data_to_treeview(self.db.df)

    def run_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請選擇要刪除的資料")
            return
        
        if not messagebox.askyesno("確認", f"確定刪除選取的 {len(selected)} 筆資料？"):
            return

        try:
            indices = [int(item) for item in selected]
            self.db.delete_rows(indices)
            self.run_search() # 重新整理
            messagebox.showinfo("成功", "資料已刪除")
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def run_save(self):
        try:
            path = self.db.save()
            messagebox.showinfo("成功", f"儲存至 {path}")
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def open_add_edit_window(self, edit_index=None):
        """彈出編輯視窗 (使用 CTkToplevel)"""
        is_edit = edit_index is not None
        
        # 建立子視窗
        win = ctk.CTkToplevel(self)
        win.title("編輯資料" if is_edit else "新增資料")
        win.geometry("400x500")
        win.grab_set() # 鎖定主視窗
        
        # 讓子視窗置頂
        win.attributes("-topmost", True)

        initial_data = {}
        if is_edit:
            initial_data = self.db.df.loc[edit_index].to_dict()

        entry_vars = {}
        
        # 內容容器
        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        for i, col in enumerate(self.db.display_cols):
            ctk.CTkLabel(frame, text=col + ":", font=("Microsoft JhengHei UI", 12)).grid(row=i*2, column=0, sticky="w", padx=10, pady=(10, 0))
            
            val = initial_data.get(col, "")
            var = tk.StringVar(value=str(val))
            
            entry = ctk.CTkEntry(frame, textvariable=var, width=250)
            entry.grid(row=i*2+1, column=0, sticky="ew", padx=10, pady=(0, 5))
            
            entry_vars[col] = var
            
            if is_edit and col == self.db.colmap.get("客戶編號"):
                entry.configure(state="disabled") # 編號不給改

        def save_action():
            data = {k: v.get() for k, v in entry_vars.items()}
            try:
                if is_edit:
                    self.db.edit_row(edit_index, data)
                else:
                    self.db.add_row(data)
                
                self.run_search() # 更新畫面
                win.destroy()
                messagebox.showinfo("成功", "資料已儲存")
            except Exception as e:
                messagebox.showerror("失敗", str(e))

        ctk.CTkButton(win, text="確認儲存", command=save_action, fg_color="#2CC985", hover_color="#229A65").pack(pady=10)

    def open_edit_window(self, event):
        sel = self.tree.selection()
        if len(sel) == 1:
            self.open_add_edit_window(int(sel[0]))

if __name__ == "__main__":
    # 預設檔案
    DEFAULT_FILE = "cust.xlsx"
    
    target_file = DEFAULT_FILE
    if not os.path.exists(target_file):
        # 沒檔案就叫使用者選
        root = tk.Tk()
        root.withdraw()
        target_file = filedialog.askopenfilename(title="選擇資料檔", filetypes=(("Excel", "*.xlsx"), ("CSV", "*.csv")))
        root.destroy()
    
    if target_file:
        app = ClientApp(target_file)
        app.mainloop()