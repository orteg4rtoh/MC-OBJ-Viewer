import sys
import os
import pyvista as pv
from pyvistaqt import BackgroundPlotter
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class MinecraftModelViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("MC OBJ Viewer Pro")
        self.resize(1200, 850)

        # Главный контейнер
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # ПАНЕЛЬ КНОПОК
        self.button_layout = QHBoxLayout()
        
        # Кнопки смены темы
        self.btn_dark = QPushButton("Dark")
        self.btn_gray = QPushButton("Gray")
        self.btn_white = QPushButton("White")
        
        # Кнопка сброса
        self.btn_reset = QPushButton("Сбросить камеру (R)")

        for btn in [self.btn_dark, self.btn_gray, self.btn_white, self.btn_reset]:
            self.button_layout.addWidget(btn)
        
        self.main_layout.addLayout(self.button_layout)

        # 3D ОКНО
        try:
            self.plotter = BackgroundPlotter(show=False)
            self.plotter.set_background("#222222") # По умолчанию темно
            self.main_layout.addWidget(self.plotter.interactor)
        except Exception as e:
            print(f"Ошибка 3D: {e}")

        # ИНФО ПАНЕЛЬ
        self.info_label = QLabel("Перетащите .obj | R — сброс | Space — центр")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px; background-color: #111; color: #00ff00; padding: 8px;")
        self.main_layout.addWidget(self.info_label)

        # Привязка событий
        self.btn_dark.clicked.connect(lambda: self.change_theme("#111111"))
        self.btn_gray.clicked.connect(lambda: self.change_theme("#444444"))
        self.btn_white.clicked.connect(lambda: self.change_theme("#ffffff"))
        self.btn_reset.clicked.connect(self.reset_cam)

        self.setAcceptDrops(True)

    def change_theme(self, color):
        self.plotter.set_background(color)
        self.info_label.setText(f"Тема изменена: {color}")

    def reset_cam(self):
        self.plotter.view_isometric()
        self.plotter.reset_camera()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R or event.key() == Qt.Key_Space:
            self.reset_cam()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        obj = next((f for f in files if f.lower().endswith('.obj')), None)
        if obj: self.load_model(obj)

    def load_model(self, path):
        self.plotter.clear()
        try:
            reader = pv.get_reader(path)
            mesh = reader.read()
            
            # Поиск текстуры
            img_path = os.path.join(os.path.dirname(path), "mvp_tracks_map.png")
            texture = pv.read_texture(img_path) if os.path.exists(img_path) else None

            if texture:
                # Включаем прозрачность через слои (Depth Peeling) - это не должно лагать
                self.plotter.enable_depth_peeling(number_of_peels=4)
                self.plotter.add_mesh(mesh, texture=texture, smooth_shading=False, pbr=False, opacity=1.0)
            else:
                self.plotter.add_mesh(mesh, color="gray", smooth_shading=False)

            # Убираем мыло
            self.plotter.render()
            for actor in self.plotter.renderer.GetActors():
                if hasattr(actor, 'GetTexture') and actor.GetTexture():
                    actor.GetTexture().SetInterpolate(0)

            self.reset_cam()
            self.info_label.setText(f"Загружено: {os.path.basename(path)}")
        except Exception as e:
            self.info_label.setText(f"Ошибка: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Чтобы кнопки везде выглядели одинаково
    window = MinecraftModelViewer()
    window.show()
    sys.exit(app.exec_())