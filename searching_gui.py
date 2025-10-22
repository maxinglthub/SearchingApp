import tkinter as tk
import pandas as pd
from tkinter import ttk, messagebox, filedialog
import sys
import os
import sv_ttk
from typing import Dict, Optional, List

# 匯入資料核心：從 searching_main 模組中導入 ClientDB
try:
    from searching_main import ClientDB
except ImportError:
    print("錯誤：找不到 searching_main.py 檔案。請確保兩個檔案在同一目錄下。")
    sys.exit(1)


class ClientApp(tk.Tk):
    def __init__(self, file_path):
        super().__init__()
        self.title("客戶資料管理系統 (Tkinter)")
        self.geometry("1000x700")

        sv_ttk.set_theme("dark")

        # 1. 載入資料核心
        self.file_path = file_path
        try:
            self.db = ClientDB(file_path)
        except Exception as e:
            messagebox.showerror("資料載入錯誤", f"無法載入檔案：{e}")
            self.destroy()
            return
            
        # 2. 設定佈局
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.create_widgets()
        
        # 3. 初始顯示
        self.load_data_to_treeview(self.db.df)

    # (此處省略 create_widgets 及其他方法的程式碼，與先前提供的一致，
    # 僅為避免冗長，請使用先前版本中的相同方法內容)
    
    def create_widgets(self):
        # 頂部：搜尋/操作區域
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.top_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.top_frame, text="搜尋關鍵字:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_entry = ttk.Entry(self.top_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Button(self.top_frame, text="🔍 搜尋", command=self.run_search).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(self.top_frame, text="🔄 重置", command=lambda: self.load_data_to_treeview(self.db.df)).grid(row=0, column=3, padx=5, pady=5)
        
        # 操作按鈕群
        self.btn_add = ttk.Button(self.top_frame, text="➕ 新增", command=lambda: self.open_add_edit_window())
        self.btn_add.grid(row=0, column=4, padx=5, pady=5)
        
        self.btn_delete = ttk.Button(self.top_frame, text="🗑️ 刪除", command=self.run_delete)
        self.btn_delete.grid(row=0, column=5, padx=5, pady=5)
        
        self.btn_save = ttk.Button(self.top_frame, text="💾 儲存", command=self.run_save)
        self.btn_save.grid(row=0, column=6, padx=(15, 5), pady=5)
        
        # 資料筆數顯示
        self.count_label = ttk.Label(self.top_frame, text=f"資料筆數：{len(self.db.df)}")
        self.count_label.grid(row=0, column=7, padx=10, pady=5, sticky="e")

        # 中間：表格顯示區域
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # 滾動條
        self.ysb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.ysb.grid(row=0, column=1, sticky="ns")
        self.xsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.xsb.grid(row=1, column=0, sticky="ew")
        
        # Treeview 本體
        self.tree = ttk.Treeview(self.tree_frame, show="headings", 
                                 yscrollcommand=self.ysb.set, xscrollcommand=self.xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.ysb.config(command=self.tree.yview)
        self.xsb.config(command=self.tree.xview)
        
        # 綁定事件 (雙擊開啟編輯)
        self.tree.bind("<Double-1>", self.open_edit_window)

    def load_data_to_treeview(self, df: pd.DataFrame):
        """將 DataFrame 內容載入到 Treeview 中。"""
        
        columns = [c for c in self.db.display_cols if c in df.columns]
        
        self.tree["columns"] = columns
        self.tree.delete(*self.tree.get_children())
            
        for col_name in columns:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=100, anchor='center') 

        for index, row in df.iterrows():
            values = [row[col] for col in columns]
            self.tree.insert("", "end", iid=index, values=values)
            
        self.count_label.config(text=f"資料筆數：{len(df)}")

    def run_search(self):
        """執行搜尋並更新表格顯示。"""
        query = self.search_entry.get().strip()
        q_words = query.split()
        
        try:
            results_df = self.db.search(q_words=q_words, use_or=False)
            self.load_data_to_treeview(results_df)
        except Exception as e:
            messagebox.showerror("搜尋錯誤", f"搜尋時發生錯誤：{e}")
            
    def run_delete(self):
        """刪除選定的行。"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "請先選取要刪除的資料行。")
            return
            
        if not messagebox.askyesno("確認刪除", f"確定要刪除選取的 {len(selected_items)} 筆資料嗎？"):
            return
            
        indices_to_delete = [int(self.tree.item(item, 'iid')) for item in selected_items]
        
        try:
            n_deleted = self.db.delete_rows(indices_to_delete)
            messagebox.showinfo("成功", f"已成功刪除 {n_deleted} 筆資料。")
            self.load_data_to_treeview(self.db.df) 
        except Exception as e:
            messagebox.showerror("刪除失敗", f"刪除時發生錯誤：{e}")


    def run_save(self):
        """儲存操作，預設覆寫原檔。"""
        try:
            saved_path = self.db.save()
            messagebox.showinfo("儲存成功", f"資料已成功儲存至：\n{saved_path}")
        except Exception as e:
            messagebox.showerror("儲存失敗", f"儲存時發生錯誤：{e}")
            
    def open_add_edit_window(self, edit_index: Optional[int] = None):
        """打開新增或編輯資料的彈出視窗。"""
        is_edit = edit_index is not None
        
        win = tk.Toplevel(self)
        win.title("編輯資料" if is_edit else "新增資料")
        win.transient(self) 
        win.grab_set() 
        
        entry_vars: Dict[str, tk.StringVar] = {}
        initial_data: Dict[str, str] = {}
        
        if is_edit:
            try:
                row_data = self.db.df.loc[edit_index]
                initial_data = row_data.to_dict()
            except KeyError:
                 messagebox.showerror("錯誤", "找不到要編輯的資料。")
                 win.destroy()
                 return
        
        for i, col_name in enumerate(self.db.display_cols):
            ttk.Label(win, text=f"{col_name}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            var = tk.StringVar(value=initial_data.get(col_name, ''))
            entry = ttk.Entry(win, textvariable=var, width=50)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entry_vars[col_name] = var
            
            if is_edit and col_name == self.db.colmap.get('客戶編號'):
                 entry.config(state='readonly')
            
        def save_action():
            data = {k: v.get() for k, v in entry_vars.items()}
            
            try:
                if is_edit:
                    self.db.edit_row(edit_index, data)
                    action = "更新"
                else:
                    self.db.add_row(data)
                    action = "新增"

                messagebox.showinfo("成功", f"資料已成功{action}！")
                self.load_data_to_treeview(self.db.df) 
                win.destroy()
            except Exception as e:
                messagebox.showerror("失敗", f"資料{action}失敗：{e}")


        ttk.Button(win, text="儲存", command=save_action).grid(row=len(self.db.display_cols), column=1, padx=5, pady=10, sticky="e")
        win.grid_columnconfigure(1, weight=1)

    def open_edit_window(self, event):
        """雙擊 Treeview 行，打開編輯視窗。"""
        selected_items = self.tree.selection()
        if len(selected_items) == 1:
            edit_index = int(self.tree.item(selected_items[0], 'iid'))
            self.open_add_edit_window(edit_index=edit_index)

# --- 程式入口點 ---
if __name__ == "__main__":
    
    # *** 變更：預設檔案路徑為 cust.xlsx ***
    DEFAULT_FILE_PATH = "cust.xlsx" 
    
    FILE_PATH = DEFAULT_FILE_PATH
    if len(sys.argv) > 1 and sys.argv[1] == "--file" and len(sys.argv) > 2:
        FILE_PATH = sys.argv[2]
    
    if not os.path.exists(FILE_PATH):
        # 彈出檔案選擇器
        print(f"預設檔案 '{FILE_PATH}' 不存在，將開啟檔案選擇器...")
        
        temp_root = tk.Tk()
        temp_root.withdraw() 
        
        selected_path = filedialog.askopenfilename(
            title="請選擇客戶資料檔案 (cust.xlsx 或其他)",
            filetypes=(("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*"))
        )
        
        temp_root.destroy()
        
        if not selected_path:
            print("未選擇檔案，程式退出。")
            sys.exit(1)
        
        FILE_PATH = selected_path

    # 執行 GUI
    try:
        app = ClientApp(FILE_PATH)
        app.mainloop()
    except Exception as e:
        print(f"應用程式啟動失敗：{e}")
        messagebox.showerror("啟動失敗", f"無法啟動應用程式或載入資料：{e}")
        sys.exit(1)

# end of searching_gui.py