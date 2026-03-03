"""中文可视化语法编码与名词块分析工具（Tkinter）。"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from Extract_nouns import VisualGrammarEncoder


class EncoderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("英文句子语法编码与名词块分析工具")
        self.root.geometry("1080x760")

        self.encoder = VisualGrammarEncoder()
        self.status_var = tk.StringVar(value="就绪：请输入英文句子或段落。")

        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            outer,
            text="英文句子视觉化语法标注编码器（中文界面）",
            font=("Microsoft YaHei", 14, "bold"),
        )
        title.pack(anchor=tk.W, pady=(0, 8))

        guide_text = (
            "操作步骤（适合零代码用户）\n"
            "1）在下方输入英文句子/段落。\n"
            "2）点击【名词块分析】查看：\n"
            "   - 两个及以上单词组成的名词块模式\n"
            "   - 单个名词 + 前后词性搭配（且不属于多词名词块）\n"
            "3）点击【导出名词分析Excel】保存到表格。\n"
            "4）如需语法编码，点击【语法编码】或【导出编码Word】。"
        )
        guide = tk.Text(outer, height=7, wrap=tk.WORD, bg="#F7F7F7")
        guide.insert("1.0", guide_text)
        guide.configure(state=tk.DISABLED)
        guide.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            outer,
            text="请输入英文文本（可多行）：",
            font=("Microsoft YaHei", 11, "bold"),
        ).pack(anchor=tk.W)

        self.input_text = tk.Text(outer, height=10, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, pady=(6, 8))

        btn_row = ttk.Frame(outer)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_row, text="语法编码", command=self.on_encode).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="名词块分析", command=self.on_noun_analyze).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="导出名词分析Excel", command=self.on_export_noun_excel).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="导出编码Word", command=self.on_export_docx).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="清空", command=self.on_clear).pack(side=tk.LEFT)

        self.output_notebook = ttk.Notebook(outer)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)

        frame_encoding = ttk.Frame(self.output_notebook)
        frame_noun = ttk.Frame(self.output_notebook)
        self.output_notebook.add(frame_encoding, text="语法编码结果")
        self.output_notebook.add(frame_noun, text="名词分析结果")

        self.encoding_output = tk.Text(frame_encoding, wrap=tk.WORD)
        self.encoding_output.pack(fill=tk.BOTH, expand=True)

        self.noun_output = tk.Text(frame_noun, wrap=tk.WORD)
        self.noun_output.pack(fill=tk.BOTH, expand=True)

        status = ttk.Label(
            outer,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(6, 4),
        )
        status.pack(fill=tk.X, pady=(8, 0))

    def _get_input(self) -> str:
        return self.input_text.get("1.0", tk.END).strip()

    def _require_input(self) -> str | None:
        text = self._get_input()
        if not text:
            messagebox.showwarning("提示", "请先输入英文句子或段落。")
            self.status_var.set("未执行：输入内容为空。")
            return None
        return text

    def on_encode(self) -> None:
        text = self._require_input()
        if text is None:
            return

        try:
            lines = self.encoder.encode_text_lines(text)
        except Exception as exc:
            messagebox.showerror("语法编码失败", str(exc))
            self.status_var.set(f"语法编码失败：{exc}")
            return

        self.encoding_output.delete("1.0", tk.END)
        self.encoding_output.insert(tk.END, "\n".join(lines))
        self.output_notebook.select(0)
        self.status_var.set(f"语法编码完成：共输出 {len(lines)} 个 token。")

    def on_noun_analyze(self) -> None:
        text = self._require_input()
        if text is None:
            return

        try:
            labeled = self.encoder.get_labeled_noun_results(text)
        except Exception as exc:
            messagebox.showerror("名词块分析失败", str(exc))
            self.status_var.set(f"名词块分析失败：{exc}")
            return

        lines: list[str] = ["【第一部分：两个及以上单词组成的名词块模式】"]
        if labeled["labeled_multiword"]:
            for i, item in enumerate(labeled["labeled_multiword"], 1):
                lines.append(
                    f"{i}. {item['句子序号']} | 名词块：{item['名词块文本']} | 模式：{item['词性组合模式']}"
                )
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("【第二部分：单个名词 + 前后词性搭配组合】")
        if labeled["labeled_single"]:
            for i, item in enumerate(labeled["labeled_single"], 1):
                lines.append(
                    f"{i}. {item['句子序号']} | 名词：{item['单个名词']} | 搭配：{item['前后词性搭配模式']}"
                )
        else:
            lines.append("(none)")

        self.noun_output.delete("1.0", tk.END)
        self.noun_output.insert(tk.END, "\n".join(lines))
        self.output_notebook.select(1)
        self.status_var.set(
            f"名词块分析完成：多词名词块 {len(labeled['labeled_multiword'])} 条，单名词搭配 {len(labeled['labeled_single'])} 条。"
        )

    def on_export_noun_excel(self) -> None:
        text = self._require_input()
        if text is None:
            return

        path = filedialog.asksaveasfilename(
            title="保存名词块分析结果",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile="名词块分析结果.xlsx",
        )
        if not path:
            self.status_var.set("已取消导出名词分析 Excel。")
            return

        try:
            saved = self.encoder.export_noun_results_to_excel(text, output_excel=path)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            self.status_var.set(f"导出名词分析 Excel 失败：{exc}")
            return

        messagebox.showinfo("导出成功", f"文件已保存：\n{saved}")
        self.status_var.set(f"名词分析 Excel 导出成功：{saved}")

    def on_export_docx(self) -> None:
        text = self._require_input()
        if text is None:
            return

        path = filedialog.asksaveasfilename(
            title="保存语法编码结果",
            defaultextension=".docx",
            filetypes=[("Word 文档", "*.docx")],
            initialfile="编码结果.docx",
        )
        if not path:
            self.status_var.set("已取消导出编码 Word。")
            return

        try:
            saved = self.encoder.save_encoded_text_to_word(text, path)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            self.status_var.set(f"导出编码 Word 失败：{exc}")
            return

        messagebox.showinfo("导出成功", f"文件已保存：\n{saved}")
        self.status_var.set(f"编码 Word 导出成功：{saved}")

    def on_clear(self) -> None:
        self.input_text.delete("1.0", tk.END)
        self.encoding_output.delete("1.0", tk.END)
        self.noun_output.delete("1.0", tk.END)
        self.status_var.set("已清空输入和输出。")


def main() -> None:
    root = tk.Tk()
    EncoderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
