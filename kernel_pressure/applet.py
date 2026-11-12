#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LinSpectacles - Linux Inspector Suite
# Copyright (C) 2026 brunonlinespace
# GPL-3.0-or-later

APPLET_ID = "linspectacles-kernel-pressure"
APPLET_NAME = "Kernel Pressure"
APPLET_VERSION = "0.0.7"
APPLET_AUTHOR = "brunonlinespace"
APPLET_EDITOR = "brunonlinespace"
APPLET_ORGANIZATION_NAME = "LinSpectacles"
APPLET_ORGANIZATION_ID = "linspectacles"
APPLET_ORGANIZATION_URL = "https://github.com/linspectacles/"
APPLET_REPOSITORY = "https://github.com/linspectacles/kernel-pressure"

from pathlib import Path

from PyQt6.QtCore import QSettings, Qt, QUrl
from PyQt6.QtGui import QColor, QKeySequence, QPixmap, QShortcut, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ._support import BaseInspectorTab, export_records_dialog, metadata_font_qss


def _parse_psi_line(text):
    """Parse one Linux PSI line without deriving a health interpretation."""
    parts = str(text or "").split()
    if not parts:
        return None

    row = {"scope": parts[0]}
    for token in parts[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        row[key] = value
    return row


def _sources_text():
    return """Kernel Pressure is read-only. Its displayed facts come directly from Linux Pressure Stall Information (PSI).

CPU pressure
------------
/proc/pressure/cpu

Memory pressure
---------------
/proc/pressure/memory

I/O pressure
------------
/proc/pressure/io

IRQ pressure (when exposed by the kernel)
-----------------------------------------
/proc/pressure/irq

Reported fields
---------------
scope   PSI 'some' or 'full' scope when exposed by the kernel; IRQ reports only 'full'.
avg10   reported 10-second pressure average.
avg60   reported 60-second pressure average.
avg300  reported 300-second pressure average.
total   cumulative stalled time reported by the kernel, in microseconds.

Interpretation
--------------
Kernel Pressure reports the PSI values exposed by the running kernel. LinSpectacles does not assign a good/bad threshold or infer system health from these values.

Access model
------------
Read-only. This applet only reads /proc/pressure/cpu, /proc/pressure/memory, /proc/pressure/io, and /proc/pressure/irq when available.
"""


def _record_details_plain_text(record):
    return "\n".join(
        [
            f"Resource: {record.get('resource') or 'Not reported'}",
            f"Scope: {record.get('scope') or 'Not reported'}",
            f"avg10: {record.get('avg10') or 'Not reported'}",
            f"avg60: {record.get('avg60') or 'Not reported'}",
            f"avg300: {record.get('avg300') or 'Not reported'}",
            f"Total stalled time (µs): {record.get('total') or 'Not reported'}",
        ]
    )


class KernelPressureOptionsDialog(QDialog):
    """Established LinSpectacles Options treatment for Kernel Pressure."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle("Options — Kernel Pressure")
        self.resize(980, 720)

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)

        # Appearance
        appearance_page = QWidget()
        appearance_layout = QVBoxLayout(appearance_page)
        appearance_layout.setContentsMargins(12, 12, 12, 12)
        appearance_layout.setSpacing(10)

        appearance_heading = QLabel("Metadata display")
        heading_font = appearance_heading.font()
        heading_font.setBold(True)
        appearance_heading.setFont(heading_font)
        appearance_layout.addWidget(appearance_heading)

        appearance_note = QLabel(
            "Choose how the inventory and Metadata Details panes are arranged. "
            "This Kernel Pressure setting is remembered."
        )
        appearance_note.setWordWrap(True)
        appearance_layout.addWidget(appearance_note)

        layout_row = QHBoxLayout()
        layout_row.addWidget(QLabel("Record details layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Horizontal", "Vertical"])
        self.layout_combo.setCurrentText(
            "Vertical" if owner.details_orientation == "vertical" else "Horizontal"
        )
        self.layout_combo.currentTextChanged.connect(self._layout_changed)
        layout_row.addWidget(self.layout_combo)
        layout_row.addStretch(1)
        appearance_layout.addLayout(layout_row)

        self.show_metadata = QCheckBox("Show Metadata Details panel (F3)")
        self.show_metadata.setChecked(owner.metadata_panel_visible)
        self.show_metadata.toggled.connect(
            lambda checked: owner.set_metadata_panel_visible(bool(checked), persist=True)
        )
        appearance_layout.addWidget(self.show_metadata)

        shortcuts_note = QLabel(
            "Shortcuts: F3 hides/restores Metadata Details; "
            "Shift+F5 refreshes the inventory; Ctrl+L toggles "
            "Horizontal/Vertical; Ctrl+/ opens Options."
        )
        shortcuts_note.setWordWrap(True)
        appearance_layout.addWidget(shortcuts_note)
        appearance_layout.addStretch(1)
        tabs.addTab(appearance_page, "Appearance")

        # Sources
        sources_page = QWidget()
        sources_layout = QVBoxLayout(sources_page)
        sources_layout.setContentsMargins(12, 12, 12, 12)
        sources_layout.setSpacing(10)

        sources_heading = QLabel("Data Sources")
        sources_heading_font = sources_heading.font()
        sources_heading_font.setBold(True)
        sources_heading_font.setPointSize(max(sources_heading_font.pointSize(), 11))
        sources_heading.setFont(sources_heading_font)
        sources_layout.addWidget(sources_heading)

        sources_note = QLabel("Linux PSI interfaces used by this read-only applet.")
        sources_note.setWordWrap(True)
        sources_layout.addWidget(sources_note)

        sources_text = QTextEdit()
        sources_text.setReadOnly(True)
        sources_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        chosen_font = getattr(owner, "_metadata_font", None)
        if chosen_font is not None:
            sources_text.setFont(chosen_font)
            sources_text.document().setDefaultFont(chosen_font)
            sources_text.setCurrentFont(chosen_font)
            font_rule = metadata_font_qss(chosen_font)
        else:
            font_rule = ""
        sources_text.setStyleSheet(
            "QTextEdit { "
            + font_rule
            + " background-color: #151719; color: #dcdcdc; "
              "border: 1px solid #333333; }"
        )

        source_heading_format = QTextCharFormat()
        source_heading_format.setForeground(QColor("#9cdcfe"))
        source_heading_format.setFontWeight(600)
        source_value_format = QTextCharFormat()
        source_value_format.setForeground(QColor("#dcdcdc"))

        # Keep the established PSI provenance wording. Only its presentation is
        # adapted to the Journal-style Sources canvas: blue section headings,
        # indented neutral-grey evidence and no plain-text underline rules.
        source_lines = _sources_text().splitlines()
        cursor = sources_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        for index, line in enumerate(source_lines):
            next_line = source_lines[index + 1] if index + 1 < len(source_lines) else ""
            is_heading = bool(next_line) and len(next_line) >= 3 and set(next_line) == {"-"}
            is_rule = len(line) >= 3 and set(line) == {"-"}
            if is_rule:
                continue
            if is_heading:
                cursor.insertText(line + "\n", source_heading_format)
            else:
                # The opening description precedes the first section; section
                # evidence is indented as in the authoritative Sources panels.
                prefix = "  " if line and index > 0 else ""
                cursor.insertText(prefix + line + "\n", source_value_format)
        sources_text.setTextCursor(cursor)
        sources_text.moveCursor(QTextCursor.MoveOperation.Start)
        sources_layout.addWidget(sources_text, 1)
        tabs.addTab(sources_page, "Sources")

        # Export
        export_page = QWidget()
        export_layout = QVBoxLayout(export_page)
        export_layout.setContentsMargins(12, 12, 12, 12)
        export_layout.setSpacing(10)

        export_heading = QLabel("Export details")
        export_heading_font = export_heading.font()
        export_heading_font.setBold(True)
        export_heading.setFont(export_heading_font)
        export_layout.addWidget(export_heading)

        export_note = QLabel("Select the Kernel Pressure details to include in the export.")
        export_note.setWordWrap(True)
        export_layout.addWidget(export_note)

        self.export_resource = QCheckBox("Resource")
        self.export_scope = QCheckBox("Scope")
        self.export_avg10 = QCheckBox("avg10")
        self.export_avg60 = QCheckBox("avg60")
        self.export_avg300 = QCheckBox("avg300")
        self.export_total = QCheckBox("Total µs")
        self.export_metadata = QCheckBox("Metadata Details")

        for checkbox in (
            self.export_resource,
            self.export_scope,
            self.export_avg10,
            self.export_avg60,
            self.export_avg300,
            self.export_total,
        ):
            checkbox.setChecked(True)
        self.export_metadata.setChecked(False)

        for checkbox in (
            self.export_resource,
            self.export_scope,
            self.export_avg10,
            self.export_avg60,
            self.export_avg300,
            self.export_total,
            self.export_metadata,
        ):
            export_layout.addWidget(checkbox)

        export_layout.addStretch(1)
        export_row = QHBoxLayout()
        export_row.addStretch(1)
        export_button = QPushButton("Export...")
        export_button.clicked.connect(self._export_selected)
        export_row.addWidget(export_button)
        export_layout.addLayout(export_row)
        tabs.addTab(export_page, "Export")

        # About
        about_page = QWidget()
        about_layout = QVBoxLayout(about_page)
        about_layout.setContentsMargins(24, 20, 24, 18)
        about_layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(112, 112)
        icon_path = Path(__file__).resolve().parent / "icon.png"
        if icon_path.is_file():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(
                        112,
                        112,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        about_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        name = QLabel("<h2 style='margin:0'>Kernel Pressure</h2>")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(name)

        version = QLabel(f"Version {APPLET_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(version)

        slogan = QLabel("<b>Expose. Explore. Explain.</b>")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(slogan)

        description = QLabel(
            "A read-only LinSpectacles applet for inspecting Linux Pressure Stall "
            "Information reported by the running kernel."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(description)

        details = QLabel(
            "<b>Build:</b> Standalone LinSpectacles applet<br>"
            "<b>Organisation ID:</b> "
            f"<a href='{APPLET_ORGANIZATION_URL}'>{APPLET_ORGANIZATION_ID}</a><br>"
            f"<b>Applet ID:</b> {APPLET_ID}"
        )
        details.setWordWrap(True)
        details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        details.setOpenExternalLinks(True)
        details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(details)

        copyright_label = QLabel(
            "Copyright © 2026 "
            "<a href='https://github.com/brunonlinespace'>brunonlinespace</a>"
        )
        copyright_label.setOpenExternalLinks(True)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(copyright_label)

        license_label = QLabel("Licensed under GNU GPLv3 or later.")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(license_label)

        license_url = QUrl.fromLocalFile(
            str(Path(__file__).resolve().parent.parent / "LICENSE")
        ).toString()
        readme_url = QUrl.fromLocalFile(
            str(Path(__file__).resolve().parent.parent / "README.md")
        ).toString()
        links = QLabel(
            f"<a href='{readme_url}'>README</a> "
            "&nbsp;·&nbsp; "
            f"<a href='{license_url}'>License</a> "
            "&nbsp;·&nbsp; "
            f"<a href='{APPLET_REPOSITORY}'>Repository</a>"
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(links)
        about_layout.addStretch(1)
        tabs.addTab(about_page, "About")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _layout_changed(self, text):
        self.owner.set_details_orientation(str(text).strip().lower(), persist=True)

    def _export_selected(self):
        selected = []
        if self.export_resource.isChecked():
            selected.append(("resource", "Resource", 110, "left"))
        if self.export_scope.isChecked():
            selected.append(("scope", "Scope", 85, "left"))
        if self.export_avg10.isChecked():
            selected.append(("avg10", "avg10", 90, "right"))
        if self.export_avg60.isChecked():
            selected.append(("avg60", "avg60", 90, "right"))
        if self.export_avg300.isChecked():
            selected.append(("avg300", "avg300", 90, "right"))
        if self.export_total.isChecked():
            selected.append(("total", "Total µs", 130, "right"))
        if self.export_metadata.isChecked():
            selected.append(("metadata_details", "Metadata Details", 520, "left"))

        if not selected:
            QMessageBox.information(self, "Export", "Select at least one detail to export.")
            return

        records = []
        for record in self.owner.get_export_records():
            item = dict(record)
            if self.export_metadata.isChecked():
                item["metadata_details"] = _record_details_plain_text(record)
            records.append(item)

        if not records:
            QMessageBox.information(self, "Export", "There is no collected data to export yet.")
            return

        path = export_records_dialog(self, APPLET_NAME, records, columns=selected)
        if path is not None:
            self.owner.set_status(f"Exported data to {path}")


class KernelPressureTab(BaseInspectorTab):
    """Read-only Linux Pressure Stall Information inspector."""

    def __init__(self, parent=None):
        columns = [
            ("resource", "Resource", 110, "left"),
            ("scope", "Scope", 85, "left"),
            ("avg10", "avg10", 90, "right"),
            ("avg60", "avg60", 90, "right"),
            ("avg300", "avg300", 90, "right"),
            ("total", "Total µs", 130, "right"),
        ]
        categories = ["All Categories", "CPU", "Memory", "I/O", "IRQ"]
        super().__init__("Total Kernel Pressure Records", columns, categories, parent)
        self.export_title = APPLET_NAME

        self.search_entry.setPlaceholderText("Search pressure records...")
        self.category_label.setText("Resource:")

        self.details_orientation = "horizontal"
        self._load_details_orientation()
        self.metadata_panel_visible = True
        self._load_metadata_panel_visibility()
        self._install_shortcuts()

        self.export_btn.setText("Options...")
        try:
            self.export_btn.clicked.disconnect()
        except TypeError:
            pass
        self.export_btn.clicked.connect(self.show_options)
        self.export_btn.setEnabled(True)

        self.load_modules()

    def show_options(self):
        dialog = KernelPressureOptionsDialog(self)
        dialog.exec()

    def _install_shortcuts(self):
        self._metadata_shortcut = QShortcut(QKeySequence("F3"), self)
        self._metadata_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._metadata_shortcut.activated.connect(self.toggle_metadata_panel)

        self._layout_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self._layout_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._layout_shortcut.activated.connect(self.toggle_details_orientation)

        self._refresh_shortcut = QShortcut(QKeySequence("Shift+F5"), self)
        self._refresh_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._refresh_shortcut.activated.connect(self.load_modules)

        self._options_shortcut = QShortcut(QKeySequence("Ctrl+/"), self)
        self._options_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._options_shortcut.activated.connect(self.show_options)

    def _load_metadata_panel_visibility(self):
        settings = QSettings("brunonlinespace", "Kernel Pressure")
        visible = settings.value("metadata_panel_visible", True)
        if isinstance(visible, str):
            visible = visible.strip().lower() not in {"0", "false", "no", "off"}
        self.set_metadata_panel_visible(bool(visible), persist=False)

    def set_metadata_panel_visible(self, visible, *, persist=True):
        self.metadata_panel_visible = bool(visible)
        panel = self.splitter.widget(1)
        if panel is not None:
            panel.setVisible(self.metadata_panel_visible)
        if persist:
            settings = QSettings("brunonlinespace", "Kernel Pressure")
            settings.setValue("metadata_panel_visible", self.metadata_panel_visible)
            settings.sync()

    def toggle_metadata_panel(self):
        self.set_metadata_panel_visible(not self.metadata_panel_visible, persist=True)

    def toggle_details_orientation(self):
        next_orientation = (
            "vertical" if self.details_orientation == "horizontal" else "horizontal"
        )
        self.set_details_orientation(next_orientation, persist=True)

    def _load_details_orientation(self):
        settings = QSettings("brunonlinespace", "Kernel Pressure")
        orientation = str(
            settings.value("details_orientation", "horizontal") or "horizontal"
        ).lower()
        if orientation not in {"horizontal", "vertical"}:
            orientation = "horizontal"
        self.set_details_orientation(orientation, persist=False)

    def set_details_orientation(self, orientation, *, persist=True):
        orientation = str(orientation or "horizontal").lower()
        if orientation not in {"horizontal", "vertical"}:
            orientation = "horizontal"
        self.details_orientation = orientation

        details_panel = self.splitter.widget(1)
        details_layout = details_panel.layout() if details_panel is not None else None
        if orientation == "vertical":
            self.splitter.setOrientation(Qt.Orientation.Vertical)
            if details_layout is not None:
                details_layout.setContentsMargins(0, 8, 0, 0)
            self.splitter.setSizes([430, 330])
        else:
            self.splitter.setOrientation(Qt.Orientation.Horizontal)
            if details_layout is not None:
                details_layout.setContentsMargins(8, 0, 0, 0)
            self.splitter.setSizes([480, 700])

        if persist:
            settings = QSettings("brunonlinespace", "Kernel Pressure")
            settings.setValue("details_orientation", orientation)
            settings.sync()

    def _filtered_records(self):
        query = self.search_entry.text().strip().lower()
        selected_resource = self.category_dropdown.currentText()
        matches = []
        for record in self.modules_data:
            match_resource = (
                selected_resource == "All Categories"
                or record.get("category") == selected_resource
            )
            match_query = not query or any(
                query in str(value).lower()
                for key, value in record.items()
                if not str(key).startswith("_")
            )
            if match_resource and match_query:
                matches.append(record)
        return matches

    def filter_modules(self, *_):
        query = self.search_entry.text().strip().lower()
        selected_resource = self.category_dropdown.currentText()
        matches = self._filtered_records()

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(matches))

        from PyQt6.QtWidgets import QTableWidgetItem

        for row, record in enumerate(matches):
            for column_index, (column_id, _label, _width, alignment) in enumerate(self.columns):
                display = str(record.get(column_id, ""))
                item = QTableWidgetItem(display)
                if column_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, record)
                if alignment == "right":
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row, column_index, item)

        self.export_btn.setEnabled(True)
        if query or selected_resource != "All Categories":
            self.filter_status_lbl.setText(
                f"(Showing {len(matches)} of {len(self.modules_data)} items)"
            )
        else:
            self.filter_status_lbl.clear()

    def load_modules(self):
        records = []
        unavailable = []
        restricted = []
        errors = []
        irq_not_exposed = False

        resource_labels = {
            "cpu": "CPU",
            "memory": "Memory",
            "io": "I/O",
            "irq": "IRQ",
        }

        for resource in ("cpu", "memory", "io", "irq"):
            path = Path("/proc/pressure") / resource
            if not path.exists():
                if resource == "irq":
                    irq_not_exposed = True
                else:
                    unavailable.append(str(path))
                continue

            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except PermissionError as exc:
                restricted.append(f"{path}: {exc}")
                continue
            except OSError as exc:
                errors.append(f"{path}: {exc}")
                continue

            label = resource_labels[resource]
            for line in text.splitlines():
                parsed = _parse_psi_line(line)
                if not parsed:
                    continue
                records.append({
                    "resource": label,
                    "category": label,
                    "scope": parsed.get("scope", ""),
                    "avg10": parsed.get("avg10", ""),
                    "avg60": parsed.get("avg60", ""),
                    "avg300": parsed.get("avg300", ""),
                    "total": parsed.get("total", ""),
                })

        self.modules_data = records
        self.stats_label.setText(
            f"Total Kernel Pressure Records: {len(self.modules_data)}"
        )
        self.filter_modules()

        if errors:
            status = (
                f"Loaded {len(records)} kernel pressure record(s); "
                f"{len(errors)} PSI source(s) returned errors."
            )
        elif restricted:
            status = (
                f"Loaded {len(records)} kernel pressure record(s); "
                f"{len(restricted)} PSI source(s) were restricted."
            )
        elif unavailable:
            status = (
                f"Loaded {len(records)} kernel pressure record(s); "
                f"{len(unavailable)} PSI source(s) were unavailable."
            )
        else:
            status = (
                f"Loaded {len(records)} kernel pressure record(s) from "
                f"{len(set(r['resource'] for r in records))} PSI resource(s)."
            )
        if irq_not_exposed:
            status += " IRQ PSI source not found at /proc/pressure/irq."
        self.set_status(status)

        if self.modules_data:
            self.table.selectRow(0)
        else:
            self.clear_info()
            self.append_info("--- Kernel Pressure Stall Information ---\n")
            self.append_info(
                "No PSI records were available from /proc/pressure on this system.\n"
            )
            self._scroll_details_to_top()

    def on_module_select(self):
        record = self.current_record()
        if not record:
            return

        self.clear_info()
        self.append_info("--- Kernel Pressure Stall Information ---\n")
        self.append_key_value("Resource", record.get("resource") or "Not reported")
        self.append_key_value("Scope", record.get("scope") or "Not reported")
        self.append_key_value("avg10", record.get("avg10") or "Not reported")
        self.append_key_value("avg60", record.get("avg60") or "Not reported")
        self.append_key_value("avg300", record.get("avg300") or "Not reported")
        self.append_key_value(
            "Total stalled time (µs)",
            record.get("total") or "Not reported",
        )
        self._scroll_details_to_top()
        self.set_status(
            f"Inspecting {record.get('resource', 'kernel')} "
            f"{record.get('scope', '')} pressure values."
        )

    def _scroll_details_to_top(self):
        cursor = self.info_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.info_text.setTextCursor(cursor)
        self.info_text.ensureCursorVisible()
        bar = self.info_text.verticalScrollBar()
        if bar is not None:
            bar.setValue(bar.minimum())


def create_applet(parent=None):
    return KernelPressureTab(parent=parent)


def run_standalone():
    import sys
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from ._support import STANDALONE_STYLESHEET

    app = QApplication(sys.argv)
    app.setApplicationName(APPLET_NAME)
    app.setOrganizationName(APPLET_ORGANIZATION_NAME)

    icon_path = Path(__file__).resolve().parent / "icon.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    app.setStyleSheet(STANDALONE_STYLESHEET)

    window = QMainWindow()
    if icon_path.is_file():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.setWindowTitle(f"{APPLET_NAME} {APPLET_VERSION} — LinSpectacles Applet")
    window.resize(1200, 780)
    window.setCentralWidget(create_applet())
    window.show()
    return app.exec()
