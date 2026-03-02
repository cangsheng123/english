"""简化版可视化语法编码界面（Tkinter）。"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from Extract_nouns import VisualGrammarEncoder


class EncoderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("English Visual Grammar Encoder")
        self.root.geometry("980x680")

        self.encoder = VisualGrammarEncoder()

        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            outer,
            text="输入英文句子或段落（可多行）：",
            font=("Arial", 11, "bold"),
        ).pack(anchor=tk.W)

        self.input_text = tk.Text(outer, height=10, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=False, pady=(6, 8))

        btn_row = ttk.Frame(outer)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(btn_row, text="编码", command=self.on_encode).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="名词块分析", command=self.on_noun_analyze).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="导出名词分析Excel", command=self.on_export_noun_excel).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="清空", command=self.on_clear).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="导出 Word(.docx)", command=self.on_export_docx).pack(side=tk.LEFT)

        ttk.Label(
            outer,
            text="编码输出（token/POS: 每字母+6位编码）：",
            font=("Arial", 11, "bold"),
        ).pack(anchor=tk.W)

        self.output_text = tk.Text(outer, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def _get_input(self) -> str:
        return self.input_text.get("1.0", tk.END).strip()

    def on_encode(self) -> None:
        text = self._get_input()
        if not text:
            messagebox.showwarning("提示", "请先输入英文句子或段落。")
            return

        try:
            lines = self.encoder.encode_text_lines(text)
        except Exception as exc:
            messagebox.showerror("编码失败", str(exc))
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "\n".join(lines))

    def on_export_docx(self) -> None:
        text = self._get_input()
        if not text:
            messagebox.showwarning("提示", "请先输入英文句子或段落。")
            return

        path = filedialog.asksaveasfilename(
            title="保存编码结果",
            defaultextension=".docx",
            filetypes=[("Word 文档", "*.docx")],
            initialfile="encoded_output.docx",
        )
        if not path:
            return

        try:
            saved = self.encoder.save_encoded_text_to_word(text, path)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return

        messagebox.showinfo("导出成功", f"文件已保存:\n{saved}")

    def on_noun_analyze(self) -> None:
        text = self._get_input()
        if not text:
            messagebox.showwarning("提示", "请先输入英文句子或段落。")
            return

        try:
            labeled = self.encoder.get_labeled_noun_results(text)
        except Exception as exc:
            messagebox.showerror("名词块分析失败", str(exc))
            return

        lines: list[str] = ["【2词及以上名词块模式】"]
        if labeled["labeled_multiword"]:
            for i, item in enumerate(labeled["labeled_multiword"], 1):
                lines.append(
                    f"{i}. {item['句子序号']} | {item['名词块文本']} | {item['词性组合模式']}"
                )
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("【单个名词+前后词性搭配组合】")
        if labeled["labeled_single"]:
            for i, item in enumerate(labeled["labeled_single"], 1):
                lines.append(
                    f"{i}. {item['句子序号']} | {item['单个名词']} | {item['前后词性搭配模式']}"
                )
        else:
            lines.append("(none)")

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "\n".join(lines))

    def on_export_noun_excel(self) -> None:
        text = self._get_input()
        if not text:
            messagebox.showwarning("提示", "请先输入英文句子或段落。")
            return

        path = filedialog.asksaveasfilename(
            title="保存名词块分析",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile="名词块分析结果.xlsx",
        )
        if not path:
            return

        try:
            saved = self.encoder.export_noun_results_to_excel(text, output_excel=path)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return

        messagebox.showinfo("导出成功", f"文件已保存:\n{saved}")

    def on_clear(self) -> None:
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)


def main() -> None:
    root = tk.Tk()
    EncoderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
