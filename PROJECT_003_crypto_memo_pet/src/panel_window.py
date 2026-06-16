"""
数据面板：密保问答、账户密码的展示与编辑
敏感字段（答案/密码）点击查看/复制时需二次输入主密码验证
"""
import tkinter as tk
from tkinter import ttk, messagebox

from data_store import add_item, update_item, delete_item, list_items, open_vault


# 两类数据的字段配置
FIELD_CONFIG = {
    "security_questions": {
        "title": "🔐 密保问答",
        "fields": [
            ("platform", "平台", "entry"),
            ("question", "问题", "entry"),
            ("answer", "答案", "secret"),
            ("note", "备注", "text"),
        ],
        "list_columns": [("平台", 160), ("问题", 280)],
        "list_keys": ["platform", "question"],
    },
    "passwords": {
        "title": "🔑 账户密码",
        "fields": [
            ("platform", "平台", "entry"),
            ("username", "用户名", "entry"),
            ("password", "密码", "secret"),
            ("url", "网址", "entry"),
            ("note", "备注", "text"),
        ],
        "list_columns": [("平台", 160), ("用户名", 200)],
        "list_keys": ["platform", "username"],
    },
}


class PanelWindow:
    """通用数据面板窗口"""

    def __init__(self, root: tk.Tk, fernet, category: str):
        self._root = root
        self._fernet = fernet
        self._category = category
        self._config = FIELD_CONFIG[category]
        self._window = None
        self._tree = None
        self._edit_fields = {}
        self._current_item_id = None
        self._is_new = False

    def show(self):
        if self._window and self._window.winfo_exists():
            self._window.lift()
            self._refresh_list()
            return

        self._window = tk.Toplevel(self._root)
        self._window.title(self._config["title"])
        self._window.geometry("700x480+150+120")
        self._window.attributes("-topmost", True)
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        main = tk.PanedWindow(self._window, orient="horizontal", sashwidth=4)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # 左侧列表
        left = tk.Frame(main)
        main.add(left, width=420)

        columns = [k for k in self._config["list_keys"]]
        self._tree = ttk.Treeview(left, columns=columns, show="headings", height=18)
        for i, (col_name, col_width) in enumerate(self._config["list_columns"]):
            self._tree.heading(columns[i], text=col_name)
            self._tree.column(columns[i], width=col_width, minwidth=60)

        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        btn_frame = tk.Frame(left)
        btn_frame.pack(fill="x", pady=(4, 0))
        tk.Button(btn_frame, text="新增", command=self._on_new,
                  font=("Microsoft YaHei UI", 9), relief="flat", bg="#4A90D9", fg="white", padx=12).pack(side="left", padx=(0, 4))
        tk.Button(btn_frame, text="删除", command=self._on_delete,
                  font=("Microsoft YaHei UI", 9), relief="flat", bg="#D94A4A", fg="white", padx=12).pack(side="left")

        # 右侧编辑区
        right = tk.Frame(main, padx=12, pady=4)
        main.add(right, width=260)

        tk.Label(right, text="编辑", font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        self._edit_frame = right
        self._edit_fields = {}
        self._build_edit_fields(right)

        edit_btn_frame = tk.Frame(right)
        edit_btn_frame.pack(fill="x", side="bottom", pady=(8, 0))
        tk.Button(edit_btn_frame, text="保存", command=self._on_save,
                  font=("Microsoft YaHei UI", 9), relief="flat", bg="#4A90D9", fg="white", padx=16).pack(side="right", padx=(4, 0))
        tk.Button(edit_btn_frame, text="清空", command=self._on_clear,
                  font=("Microsoft YaHei UI", 9), relief="flat", padx=12).pack(side="right")

        self._refresh_list()

    def _build_edit_fields(self, parent):
        for key, label, field_type in self._config["fields"]:
            tk.Label(parent, text=label, font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(6, 0))

            if field_type == "entry":
                widget = tk.Entry(parent, font=("Microsoft YaHei UI", 10), width=28)
                widget.pack(fill="x")
                self._edit_fields[key] = widget

            elif field_type == "secret":
                secret_frame = tk.Frame(parent)
                secret_frame.pack(fill="x")

                # 敏感字段默认隐藏，显示为 ●●●●●
                widget = tk.Entry(secret_frame, show="●", font=("Microsoft YaHei UI", 10), width=22)
                widget.pack(side="left", fill="x", expand=True)

                # 👁 查看（需输密码）
                btn_show = tk.Button(secret_frame, text="👁", width=3, relief="flat",
                                     command=lambda e=widget: self._require_password_to_view(e))
                btn_show.pack(side="right", padx=(2, 0))

                # 📋 复制（需输密码）
                btn_copy = tk.Button(secret_frame, text="📋", width=3, relief="flat",
                                     command=lambda e=widget: self._require_password_to_copy(e))
                btn_copy.pack(side="right", padx=(2, 0))

                self._edit_fields[key] = widget

            elif field_type == "text":
                widget = tk.Text(parent, font=("Microsoft YaHei UI", 10), height=3, width=28, wrap="word")
                widget.pack(fill="x")
                self._edit_fields[key] = widget

    def _require_password_for_secret(self) -> bool:
        """
        二次密码验证：查看/复制敏感字段前要求重新输入主密码。
        返回 True 表示验证通过，False 表示取消或错误。
        """
        from password_dialog import UnlockDialog
        dialog = UnlockDialog(self._root, error_msg="")
        password = dialog.show()
        if password is None:
            return False  # 用户取消

        # 调用 open_vault 验证密码是否正确
        fernet, err = open_vault(password)
        return fernet is not None

    def _require_password_to_view(self, entry: tk.Entry):
        """👁 查看明文：先验密码，再切换显示"""
        if not self._require_password_for_secret():
            return  # 密码错误或取消

        if entry.cget("show") == "●":
            entry.configure(show="")
        else:
            entry.configure(show="●")

    def _require_password_to_copy(self, entry: tk.Entry):
        """📋 复制到剪贴板：先验密码，再复制"""
        if not self._require_password_for_secret():
            return  # 密码错误或取消

        content = entry.get()
        if content:
            self._window.clipboard_clear()
            self._window.clipboard_append(content)
            # 提示已复制
            self._flash_copy_hint(entry)

    def _flash_copy_hint(self, entry: tk.Entry):
        """复制成功后短暂提示"""
        original_bg = entry.cget("bg")
        entry.configure(bg="#d4edda")  # 浅绿
        entry.after(800, lambda: entry.configure(bg=original_bg or "#ffffff"))

    def _toggle_secret(self, entry: tk.Entry):
        """普通切换（保留给非敏感场景）"""
        if entry.cget("show") == "●":
            entry.configure(show="")
        else:
            entry.configure(show="●")

    def _copy_to_clipboard(self, entry: tk.Entry):
        content = entry.get()
        if content:
            self._window.clipboard_clear()
            self._window.clipboard_append(content)
            self._flash_copy_hint(entry)

    def _get_field_value(self, key: str) -> str:
        widget = self._edit_fields.get(key)
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c")
        elif isinstance(widget, tk.Entry):
            return widget.get()
        return ""

    def _set_field_value(self, key: str, value: str):
        widget = self._edit_fields.get(key)
        if isinstance(widget, tk.Text):
            widget.delete("1.0", "end")
            widget.insert("1.0", value or "")
        elif isinstance(widget, tk.Entry):
            widget.delete(0, "end")
            widget.insert(0, value or "")

    def _clear_fields(self):
        for key, widget in self._edit_fields.items():
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
            elif isinstance(widget, tk.Entry):
                widget.delete(0, "end")

    def _refresh_list(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        items = list_items(self._fernet, self._category)
        for item in items:
            values = [item.get(k, "") for k in self._config["list_keys"]]
            self._tree.insert("", "end", iid=item["id"], values=values)

    def _on_select(self, event):
        selected = self._tree.selection()
        if not selected:
            return
        item_id = selected[0]
        self._current_item_id = item_id
        self._is_new = False
        items = list_items(self._fernet, self._category)
        for item in items:
            if item["id"] == item_id:
                for key, _, _ in self._config["fields"]:
                    self._set_field_value(key, item.get(key, ""))
                break

    def _on_new(self):
        self._current_item_id = None
        self._is_new = True
        self._clear_fields()

    def _on_delete(self):
        if not self._current_item_id:
            messagebox.showinfo("提示", "请先选择要删除的条目", parent=self._window)
            return
        if not messagebox.askyesno("确认", "确定要删除此条目吗？", parent=self._window):
            return
        delete_item(self._fernet, self._category, self._current_item_id)
        self._current_item_id = None
        self._is_new = False
        self._clear_fields()
        self._refresh_list()

    def _on_save(self):
        item_data = {}
        for key, _, _ in self._config["fields"]:
            item_data[key] = self._get_field_value(key)

        first_key = self._config["fields"][0][0]
        if not item_data.get(first_key):
            messagebox.showinfo("提示", f"请填写{self._config['fields'][0][1]}", parent=self._window)
            return

        if self._is_new or not self._current_item_id:
            add_item(self._fernet, self._category, item_data)
            self._is_new = False
        else:
            update_item(self._fernet, self._category, self._current_item_id, item_data)

        self._refresh_list()

    def _on_clear(self):
        self._clear_fields()
        self._current_item_id = None
        self._is_new = False

    def _on_close(self):
        if self._window:
            self._window.destroy()
            self._window = None
