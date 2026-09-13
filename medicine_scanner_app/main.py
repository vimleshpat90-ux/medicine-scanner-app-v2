"""
main.py
Medicine Scanner - Android app (Kivy)
By Vimlesh Patel

Screens:
  1. SplashScreen   - app intro
  2. HomeScreen      - list of scanned medicines (edit/delete), bottom nav
  3. AddEditScreen    - add manually / edit an existing entry (with delete)
  4. ScanScreen       - camera capture -> OCR -> auto-fill (with confidence check)
  5. ReportsScreen    - gallery of previously generated PDFs
  6. PDFExportScreen  - header (Received by / Date / Sent by) + merged table + Download/Share

Run on desktop for testing:
    pip install -r requirements.txt
    python main.py

Package for Android:
    buildozer -v android debug   (needs buildozer.spec, included)
"""

import os
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from kivy.utils import platform

import database
import names_store
import pdf_export
import ocr_match

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_OUTPUT_DIR = os.path.join(APP_DIR, "reports")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


KV = """
#:import dp kivy.metrics.dp

<Card@BoxLayout>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(78)
    padding: dp(10)
    canvas.before:
        Color:
            rgba: 0.95, 0.96, 0.98, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

ScreenManager:
    id: sm
    SplashScreen:
    HomeScreen:
    AddEditScreen:
    ScanScreen:
    ReportsScreen:
    PDFExportScreen:


<SplashScreen>:
    name: "splash"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.85, 0.9, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
        Label:
            text: "[b]Medicine Scanner[/b]"
            markup: True
            font_size: "26sp"
            color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: dp(40)
        Label:
            text: "Scan. Identify. Stay informed."
            color: 0.3, 0.3, 0.3, 1
            size_hint_y: None
            height: dp(24)
        BoxLayout:
        Button:
            text: "Get started"
            size_hint: 0.8, None
            height: dp(48)
            pos_hint: {"center_x": 0.5}
            on_release: app.root.current = "home"
        Label:
            text: "Created by Vimlesh Patel"
            color: 0.2, 0.4, 0.9, 1
            size_hint_y: None
            height: dp(40)


<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        BoxLayout:
            size_hint_y: None
            height: dp(90)
            orientation: "vertical"
            canvas.before:
                Color:
                    rgba: 0.85, 0.9, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "Medicine scans"
                font_size: "20sp"
                bold: True
                color: 0.1, 0.1, 0.1, 1
            Label:
                text: "By Vimlesh Patel"
                font_size: "13sp"
                color: 0.3, 0.3, 0.3, 1

        ScrollView:
            BoxLayout:
                id: medicine_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(70)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: 0.93, 0.93, 0.95, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Reports"
                on_release: app.root.current = "reports"
            Button:
                text: "Scan"
                on_release: app.root.current = "scan"
            Button:
                text: "Add manually"
                on_release: app.open_add_edit(None)


<AddEditScreen>:
    name: "add_edit"
    name_input: name_input
    batch_input: batch_input
    expiry_input: expiry_input
    strips_input: strips_input
    per_strip_input: per_strip_input
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            Button:
                text: "< Back"
                size_hint_x: None
                width: dp(80)
                on_release: app.root.current = "home"
            Label:
                text: "Add / edit medicine"
                bold: True
            Button:
                text: "Delete"
                size_hint_x: None
                width: dp(80)
                background_color: 0.9, 0.3, 0.3, 1
                on_release: app.delete_current_item()

        Label:
            text: "Medicine name"
            size_hint_y: None
            height: dp(20)
            halign: "left"
        TextInput:
            id: name_input
            size_hint_y: None
            height: dp(44)
            multiline: False

        Label:
            text: "Batch no."
            size_hint_y: None
            height: dp(20)
        TextInput:
            id: batch_input
            size_hint_y: None
            height: dp(44)
            multiline: False

        Label:
            text: "Expiry date (MM/YYYY)"
            size_hint_y: None
            height: dp(20)
        TextInput:
            id: expiry_input
            size_hint_y: None
            height: dp(44)
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: dp(44)
            spacing: dp(10)
            TextInput:
                id: strips_input
                hint_text: "Strips"
                multiline: False
            TextInput:
                id: per_strip_input
                hint_text: "Qty per strip"
                multiline: False

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(10)
            Button:
                text: "Cancel"
                on_release: app.root.current = "home"
            Button:
                text: "Save"
                on_release: app.save_medicine()


<ScanScreen>:
    name: "scan"
    result_label: result_label
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.1, 0.1, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Button:
                text: "X"
                size_hint_x: None
                width: dp(50)
                on_release: app.root.current = "home"
            Label:
                text: "Scan medicine"
                color: 1, 1, 1, 1

        Label:
            text: "[Camera preview here]\\n(tap capture to pick a photo)"
            color: 1, 1, 1, 0.8
            halign: "center"

        Label:
            id: result_label
            text: ""
            color: 0.6, 1, 0.6, 1
            size_hint_y: None
            height: dp(160)
            halign: "left"
            valign: "top"
            text_size: self.width, None

        BoxLayout:
            size_hint_y: None
            height: dp(90)
            padding: dp(10)
            Button:
                text: "Capture / choose photo"
                on_release: app.run_scan()


<ReportsScreen>:
    name: "reports"
    report_list: report_list
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            Button:
                text: "< Back"
                size_hint_x: None
                width: dp(80)
                on_release: app.root.current = "home"
            Label:
                text: "Reports (last 30 days)"
                bold: True
        ScrollView:
            BoxLayout:
                id: report_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
        Button:
            text: "+ Create new PDF from current list"
            size_hint_y: None
            height: dp(48)
            on_release: app.root.current = "pdf_export"


<PDFExportScreen>:
    name: "pdf_export"
    received_by_input: received_by_input
    sent_by_label: sent_by_label
    table_preview: table_preview
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(8)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            Button:
                text: "< Back"
                size_hint_x: None
                width: dp(80)
                on_release: app.root.current = "home"
            Label:
                text: "Export as PDF"
                bold: True

        Label:
            text: "Received by"
            size_hint_y: None
            height: dp(18)
        TextInput:
            id: received_by_input
            size_hint_y: None
            height: dp(42)
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(10)
            Label:
                text: "Date: " + root.today_str
            Spinner:
                id: sent_by_label
                text: app.sent_by_names[0] if app.sent_by_names else "Add name"
                values: app.sent_by_names + ["+ Add new name"]
                on_text: app.on_sent_by_selected(self.text)

        ScrollView:
            BoxLayout:
                id: table_preview
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(4)

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(10)
            Button:
                text: "Share"
                on_release: app.share_pdf()
            Button:
                text: "Download"
                on_release: app.download_pdf()
"""


class SplashScreen(Screen):
    pass


class HomeScreen(Screen):
    def on_pre_enter(self):
        self.refresh_list()

    def refresh_list(self):
        app = App.get_running_app()
        container = self.ids.medicine_list
        container.clear_widgets()
        for item in database.get_all_medicines(days=30):
            container.add_widget(app.build_medicine_card(item))


class AddEditScreen(Screen):
    current_item_id = None

    def load_item(self, item_id=None):
        self.current_item_id = item_id
        if item_id:
            item = database.get_medicine(item_id)
            self.name_input.text = item["name"]
            self.batch_input.text = item["batch_no"]
            self.expiry_input.text = item["expiry"] or ""
            self.strips_input.text = str(item["strips"])
            self.per_strip_input.text = str(item["per_strip"])
        else:
            self.name_input.text = ""
            self.batch_input.text = ""
            self.expiry_input.text = ""
            self.strips_input.text = "1"
            self.per_strip_input.text = "1"


class ScanScreen(Screen):
    pass


class ReportsScreen(Screen):
    def on_pre_enter(self):
        self.refresh_reports()

    def refresh_reports(self):
        from kivy.uix.button import Button
        container = self.ids.report_list
        container.clear_widgets()
        if not os.path.isdir(PDF_OUTPUT_DIR):
            return
        for fname in sorted(os.listdir(PDF_OUTPUT_DIR), reverse=True):
            if fname.lower().endswith(".pdf"):
                btn = Button(text=fname, size_hint_y=None, height=44)
                container.add_widget(btn)


class PDFExportScreen(Screen):
    today_str = StringProperty(datetime.now().strftime("%d %b %Y"))

    def on_pre_enter(self):
        self.refresh_table()

    def refresh_table(self):
        from kivy.uix.label import Label
        app = App.get_running_app()
        container = self.ids.table_preview
        container.clear_widgets()

        header = Label(
            text="S.No | Medicine name | Batch | Exp | Qty",
            size_hint_y=None, height=28, bold=True,
        )
        container.add_widget(header)

        rows = database.get_all_medicines(days=30)
        merged = pdf_export.merge_medicines(rows) if rows else []
        for i, r in enumerate(merged, start=1):
            line = f"{i}. {r['name']} | {r['batch_no']} | {r['expiry']} | {r['qty']}"
            container.add_widget(Label(text=line, size_hint_y=None, height=26))


class MedicineScannerApp(App):
    sent_by_names = ListProperty([])

    def build(self):
        database.init_db()
        self.sent_by_names = names_store.load_names()
        return Builder.load_string(KV)

    # ---------- Home screen: medicine card widget ----------
    def build_medicine_card(self, item):
        card = BoxLayout(orientation="vertical", size_hint_y=None, height=90, padding=8, spacing=2)

        top_row = BoxLayout(size_hint_y=None, height=26)
        from kivy.uix.label import Label
        from kivy.uix.button import Button

        top_row.add_widget(Label(text=f"[b]{item['name']}[/b]", markup=True, halign="left"))
        edit_btn = Button(text="Edit", size_hint_x=None, width=60)
        edit_btn.bind(on_release=lambda *_: self.open_add_edit(item["id"]))
        delete_btn = Button(text="Delete", size_hint_x=None, width=70)
        delete_btn.bind(on_release=lambda *_: self.delete_item(item["id"]))
        top_row.add_widget(edit_btn)
        top_row.add_widget(delete_btn)
        card.add_widget(top_row)

        qty = item["strips"] * item["per_strip"]
        details = Label(
            text=f"Batch: {item['batch_no']}   Qty: {qty}   Expiry: {item['expiry']}",
            size_hint_y=None, height=24, font_size="12sp",
        )
        card.add_widget(details)
        return card

    def open_add_edit(self, item_id):
        screen = self.root.get_screen("add_edit")
        screen.load_item(item_id)
        self.root.current = "add_edit"

    def save_medicine(self):
        screen = self.root.get_screen("add_edit")
        name = screen.name_input.text.strip()
        batch = screen.batch_input.text.strip()
        expiry = screen.expiry_input.text.strip()
        try:
            strips = int(screen.strips_input.text or 1)
            per_strip = int(screen.per_strip_input.text or 1)
        except ValueError:
            strips, per_strip = 1, 1

        if not name or not batch:
            return  # medicine name & batch no. are required

        if screen.current_item_id:
            database.update_medicine(screen.current_item_id, name, batch, expiry, strips, per_strip)
        else:
            database.add_medicine(name, batch, expiry, strips, per_strip, source="manual")

        self.root.current = "home"

    def delete_current_item(self):
        screen = self.root.get_screen("add_edit")
        if screen.current_item_id:
            database.delete_medicine(screen.current_item_id)
        self.root.current = "home"

    def delete_item(self, item_id):
        database.delete_medicine(item_id)
        self.root.get_screen("home").refresh_list()

    # ---------- Scan screen ----------
    def run_scan(self):
        """
        In a real Android build this opens the camera (via plyer / Kivy Camera)
        and passes the captured photo path to ocr_match.analyze_scan().
        Here we simulate picking a photo for the demo.
        """
        screen = self.root.get_screen("scan")
        demo_image = os.path.join(APP_DIR, "data", "sample_label.jpg")

        if os.path.exists(demo_image) and ocr_match.OCR_AVAILABLE:
            result = ocr_match.analyze_scan(demo_image)
        else:
            # fallback demo result so the flow can be tested without a real photo
            result = {
                "name": "Paracetamol 500mg", "name_confidence": 0.96, "name_needs_review": False,
                "batch_no": "B4021", "batch_needs_review": False,
                "expiry": "08/2027", "expiry_needs_review": False,
                "strips": 25, "per_strip": 15, "qty_needs_review": False,
            }

        review_flags = []
        if result["name_needs_review"]:
            review_flags.append("name")
        if result["batch_needs_review"]:
            review_flags.append("batch no.")
        if result["expiry_needs_review"]:
            review_flags.append("expiry")
        if result["qty_needs_review"]:
            review_flags.append("quantity")

        review_text = f"\\nPlease verify: {', '.join(review_flags)}" if review_flags else "\\nAll fields high confidence."
        screen.result_label.text = (
            f"Name: {result['name']}\\nBatch: {result['batch_no']}\\n"
            f"Expiry: {result['expiry']}\\nQty: {result['strips']} x {result['per_strip']}"
            f"{review_text}"
        )

        database.add_medicine(
            result["name"], result["batch_no"], result["expiry"],
            result["strips"], result["per_strip"], source="scan",
        )

    # ---------- PDF export screen ----------
    def on_sent_by_selected(self, value):
        if value == "+ Add new name":
            self.show_add_name_popup()

    def show_add_name_popup(self):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button

        text_input = TextInput(hint_text="Enter name", multiline=False, size_hint_y=None, height=44)
        save_btn = Button(text="Save name", size_hint_y=None, height=44)

        box.add_widget(text_input)
        box.add_widget(save_btn)

        popup = Popup(title="Add new sender name", content=box, size_hint=(0.8, 0.35))

        def on_save(*_):
            name = text_input.text.strip()
            if name:
                self.sent_by_names = names_store.add_name(name)
            popup.dismiss()

        save_btn.bind(on_release=on_save)
        popup.open()

    def _current_output_path(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(PDF_OUTPUT_DIR, f"medicine_report_{stamp}.pdf")

    def _build_pdf(self):
        screen = self.root.get_screen("pdf_export")
        rows = database.get_all_medicines(days=30)
        received_by = screen.received_by_input.text.strip()
        sent_by = screen.sent_by_label.text
        if sent_by == "+ Add new name":
            sent_by = ""
        output_path = self._current_output_path()
        return pdf_export.generate_pdf(rows, received_by=received_by, sent_by=sent_by,
                                        output_path=output_path)

    def download_pdf(self):
        path = self._build_pdf()
        print(f"PDF saved to: {path}")
        # On Android, plyer.storagepath / MediaStore would be used to save
        # to the Downloads folder. On desktop this just writes to /reports.

    def share_pdf(self):
        path = self._build_pdf()
        if platform == "android":
            try:
                from plyer import share
                share.share(title="Medicine report", text="Medicine scan report", filepath=path)
            except Exception as e:
                print("Share failed:", e)
        else:
            print(f"(Desktop demo) Would share file: {path}")


if __name__ == "__main__":
    MedicineScannerApp().run()
