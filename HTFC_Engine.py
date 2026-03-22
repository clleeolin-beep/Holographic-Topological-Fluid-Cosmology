import sys
import os
import tempfile
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import cKDTree

# 強制開啟硬體加速與記憶體優化
sys.argv.extend(["--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--enable-native-gpu-memory-buffers"])

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QColorDialog, QLabel, 
                             QFrame, QSlider, QComboBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt

class HolographicFluidCosmologyEngine:
    """
    全像拓撲流體宇宙學 (HTFC) - 官方 3D 物理觀測鏡
    結合 Lazy Loading 效能極限與 P_kin, P_tension, P_topo 三位一體壓強矩陣運算
    """
    def __init__(self, bg_color='#02040A', grid_color='#00FFFF', 
                 particle_color='#C8C8C8', text_color='#FFFF00',
                 bg_opacity=95, grid_opacity=15):
        
        self.bg_color = f"rgba({int(bg_color[1:3], 16)}, {int(bg_color[3:5], 16)}, {int(bg_color[5:7], 16)}, {bg_opacity/100.0})"
        self.grid_color = f"rgba({int(grid_color[1:3], 16)}, {int(grid_color[3:5], 16)}, {int(grid_color[5:7], 16)}, {grid_opacity/100.0})"
        self.particle_color = f"rgba({int(particle_color[1:3], 16)}, {int(particle_color[3:5], 16)}, {int(particle_color[5:7], 16)}, 0.4)"
        self.text_color = text_color

        # 完美對齊論文架構的 17 階觀測尺度
        self.levels = [
            "01. 微觀拓撲死結 (P_tension 表面張力鎖死)", "02. 太陽系全貌", "03. 獵戶座旋臂局部", 
            "04. 銀河系全貌 (P_kin_z 下沉壓與黏滯剪切取代暗物質)", "05. 銀河系與衛星星系", 
            "06. 本星系群局部", "07. 本星系群全貌 (局部流體鞍點)", "08. 周邊星系群",
            "09. 室女座超星系團局部", "10. 室女座超星系團骨架", "11. 拉尼亞凱亞次級網絡", 
            "12. 拉尼亞凱亞核心 (主沉降匯 Condensation Sink)", "13. 拉尼亞凱亞全貌", "14. 周邊超星系團",
            "15. 巨型宇宙網", "16. 可觀測宇宙 (CMB 全像薄膜與 P_topo 莫比烏斯噴發)",
            "17. 論文實證：全尺度無縫橋接 (Macro-to-Micro Bridge)" 
        ]

        # 宇宙地標字典 (全要素定義)
        self.landmarks = {
            'local_group': {'pos': (0, 0, 0), 'color': '#00FF00', 'name': '本星系群 (Local Group)', 'size': 6, 'symbol': 'diamond'},
            'laniakea': {'pos': (150, -50, 40), 'color': '#FFAA00', 'name': '拉尼亞凱亞核心 (Laniakea Sink)', 'size': 12, 'symbol': 'diamond'},
            'hcb_wall': {'pos': (2000, 1500, -1000), 'color': '#FF0055', 'name': '北冕座長城 (HCB Great Wall - 湧升源)', 'size': 18, 'symbol': 'square'},
            'ton_618': {'pos': (-1500, 900, -1000), 'color': '#8800FF', 'name': 'TON 618 (深淵拓撲死結)', 'size': 14, 'symbol': 'x'}
        }

    def _create_landmark_trace(self, lm_key):
        lm = self.landmarks[lm_key]
        return go.Scatter3d(
            x=[lm['pos'][0]], y=[lm['pos'][1]], z=[lm['pos'][2]], 
            mode='markers+text', 
            marker=dict(size=lm['size'], color=lm['color'], symbol=lm['symbol'], line=dict(color='white', width=1)), 
            text=[lm['name']], textposition="top center", 
            textfont=dict(color=self.text_color, size=11), 
            hoverinfo='text', hovertext=[f"<b>{lm['name']}</b><br>流體座標: {lm['pos']}"], 
            name=lm['name'], showlegend=False
        )

    def _generate_cmb_holographic_nodes(self, radius, num_hotspots=40, num_coldspots=40):
        """【論文實證 II】：CMB 全像編碼網路節點生成"""
        # 紅點：P_topo 莫比烏斯湧升源 (Hotspots)
        phi_h = np.arccos(1 - 2 * np.random.uniform(0, 1, num_hotspots)); theta_h = np.random.uniform(0, 2*np.pi, num_hotspots)
        hx = radius * np.sin(phi_h) * np.cos(theta_h); hy = radius * np.sin(phi_h) * np.sin(theta_h); hz = radius * np.cos(phi_h)
        hotspots = [{'pos': (x,y,z), 'intensity': np.random.uniform(100, 300)} for x,y,z in zip(hx,hy,hz)]

        # 藍點：P_kin 流體沉降匯 (Coldspots)
        radius_inner = radius * 0.95
        phi_c = np.arccos(1 - 2 * np.random.uniform(0, 1, num_coldspots)); theta_c = np.random.uniform(0, 2*np.pi, num_coldspots)
        cx = radius_inner * np.sin(phi_c) * np.cos(theta_c); cy = radius_inner * np.sin(phi_c) * np.sin(theta_c); cz = radius_inner * np.cos(phi_c)
        coldspots = [{'pos': (x,y,z), 'intensity': np.random.uniform(150, 400)} for x,y,z in zip(cx,cy,cz)]
        return hotspots, coldspots

    def _calculate_htfc_streamlines(self, field_type, scale, point_density=120, extra_data=None):
        """
        【論文核心】：流體跡線與三位一體壓強矩陣計算
        此函式直接對應論文公式: grad_P_total = grad_P_kin + grad_P_tension + grad_P_topo
        """
        streams = []
        
        # -------------------------------------------------------------
        # Level 16: CMB 全像網絡 (純宏觀壓強: P_topo 排斥 + P_kin 吸引)
        # -------------------------------------------------------------
        if field_type == 'cmb_holographic':
            hotspots, coldspots = extra_data
            steps = 80; dt = scale / (steps * 0.5)
            for hotspot in hotspots:
                for _ in range(int(point_density / len(hotspots))):
                    sx, sy, sz = hotspot['pos'][0] + np.random.normal(0, scale*0.05), hotspot['pos'][1] + np.random.normal(0, scale*0.05), hotspot['pos'][2] + np.random.normal(0, scale*0.05)
                    path_x, path_y, path_z = [sx], [sy], [sz]; cx, cy, cz = sx, sy, sz
                    
                    for _ in range(steps):
                        grad_P_total_x, grad_P_total_y, grad_P_total_z = 0, 0, 0
                        
                        # 1. P_topo: 紅點拓撲排斥壓 (向外湧升)
                        for hs in hotspots:
                            dx, dy, dz = cx - hs['pos'][0], cy - hs['pos'][1], cz - hs['pos'][2]
                            dist = np.sqrt(dx**2 + dy**2 + dz**2) + 1e-5
                            grad_P_topo = hs['intensity'] / (dist**2.0) 
                            grad_P_total_x += (dx/dist) * grad_P_topo; grad_P_total_y += (dy/dist) * grad_P_topo; grad_P_total_z += (dz/dist) * grad_P_topo
                            
                        # 2. P_kin: 藍點宇宙靜壓 (向內沉降)
                        for cs in coldspots:
                            dx, dy, dz = cs['pos'][0] - cx, cs['pos'][1] - cy, cs['pos'][2] - cz
                            dist = np.sqrt(dx**2 + dy**2 + dz**2) + 1e-5
                            grad_P_kin = cs['intensity'] / (dist**1.8) 
                            grad_P_total_x += (dx/dist) * grad_P_kin; grad_P_total_y += (dy/dist) * grad_P_kin; grad_P_total_z += (dz/dist) * grad_P_kin
                            
                        f_mag = np.sqrt(grad_P_total_x**2 + grad_P_total_y**2 + grad_P_total_z**2) + 1e-10
                        cx += (grad_P_total_x / f_mag) * dt; cy += (grad_P_total_y / f_mag) * dt; cz += (grad_P_total_z / f_mag) * dt
                        path_x.append(cx); path_y.append(cy); path_z.append(cz)
                    streams.append((path_x, path_y, path_z))
            return streams

        # -------------------------------------------------------------
        # Level 17: 全尺度橋接 (微觀 P_tension Z軸下沉 與 宏觀壓強的高斯疊加)
        # -------------------------------------------------------------
        elif field_type == 'bridged':
            seeds = np.random.uniform(-scale, scale, (point_density, 3))
            steps = 80; dt = scale / (steps * 1.2)
            lm_hcb = self.landmarks['hcb_wall']['pos']; lm_laniakea = self.landmarks['laniakea']['pos']; lm_ton = self.landmarks['ton_618']['pos']
            R_influence = 300.0 # 拓撲死結影響半徑
            
            for seed in seeds:
                path_x, path_y, path_z = [seed[0]], [seed[1]], [seed[2]]
                cx, cy, cz = seed[0], seed[1], seed[2]
                
                for _ in range(steps):
                    # A. 宏觀壓強 (P_topo 湧出 + P_kin 匯聚)
                    dx_h, dy_h, dz_h = cx - lm_hcb[0], cy - lm_hcb[1], cz - lm_hcb[2]
                    dist_h = np.sqrt(dx_h**2 + dy_h**2 + dz_h**2) + 1e-5
                    P_topo_out = 1.0e6 / (dist_h**1.8)
                    grad_macro_x = (dx_h/dist_h) * P_topo_out; grad_macro_y = (dy_h/dist_h) * P_topo_out; grad_macro_z = (dz_h/dist_h) * P_topo_out

                    dx_l, dy_l, dz_l = lm_laniakea[0] - cx, lm_laniakea[1] - cy, lm_laniakea[2] - cz
                    dist_l = np.sqrt(dx_l**2 + dy_l**2 + dz_l**2) + 1e-5
                    P_kin_in = 8.0e5 / (dist_l**1.5)
                    grad_macro_x += (dx_l/dist_l) * P_kin_in; grad_macro_y += (dy_l/dist_l) * P_kin_in; grad_macro_z += (dz_l/dist_l) * P_kin_in

                    # B. 微觀死結壓強 (P_tension 引發的 Z 軸極區下沉與翻湧)
                    dx_t, dy_t, dz_t = lm_ton[0] - cx, lm_ton[1] - cy, lm_ton[2] - cz
                    dist_t = np.sqrt(dx_t**2 + dy_t**2 + dz_t**2) + 1e-5
                    H_thickness = 150.0 * np.exp(-(dist_t/(R_influence*0.3))**2) + 10.0
                    grad_micro_z = (dz_t / H_thickness**2) * 50.0  # P_kin_z 極端壓縮
                    
                    theta_angle = np.arctan2(dy_t, dx_t)
                    roll_phase = dist_t * 0.5 - theta_angle * 3.0
                    roll_intensity = 80.0 * np.exp(-(dist_t - R_influence*0.5)**2 / (R_influence*0.2)**2)
                    grad_micro_z += np.cos(roll_phase) * roll_intensity
                    vortex_r = np.sin(roll_phase) * roll_intensity * np.sign(dz_t)
                    
                    grad_micro_x = (dx_t / dist_t**1.1) * 30.0 + (dx_t/dist_t) * vortex_r
                    grad_micro_y = (dy_t / dist_t**1.1) * 30.0 + (dy_t/dist_t) * vortex_r

                    # C. 論文核心：連續介質尺度權重疊加
                    W = np.exp(-(dist_t / R_influence)**2)
                    fx = (1.0 - W) * grad_macro_x + W * grad_micro_x
                    fy = (1.0 - W) * grad_macro_y + W * grad_micro_y
                    fz = (1.0 - W) * grad_macro_z + W * grad_micro_z

                    f_mag = np.sqrt(fx**2 + fy**2 + fz**2) + 1e-10
                    cx += (fx / f_mag) * dt; cy += (fy / f_mag) * dt; cz += (fz / f_mag) * dt
                    path_x.append(cx); path_y.append(cy); path_z.append(cz)
                    if dist_l < dt * 2 or dist_t < dt * 1.5: break

                streams.append((path_x, path_y, path_z))
            return streams

    def _draw_batch_streamlines(self, streams, color, thickness=1.5):
        all_x, all_y, all_z = [], [], []
        for path in streams:
            all_x.extend(path[0] + [None]); all_y.extend(path[1] + [None]); all_z.extend(path[2] + [None])
        return [go.Scatter3d(x=all_x, y=all_y, z=all_z, mode='lines', line=dict(color=color, width=thickness), hoverinfo='none', showlegend=False)]

    def build_level_traces(self, level_idx):
        """Lazy Loading 架構：只渲染當前選取的階層，釋放記憶體"""
        t = []
        
        # Level 16: 可觀測宇宙 (CMB)
        if level_idx == 15:
            sim_scale = 5000.0
            t.append(self._create_landmark_trace('local_group'))
            hotspots, coldspots = self._generate_cmb_holographic_nodes(sim_scale, 60, 60)
            
            hx = [h['pos'][0] for h in hotspots]; hy = [h['pos'][1] for h in hotspots]; hz = [h['pos'][2] for h in hotspots]
            t.append(go.Scatter3d(x=hx, y=hy, z=hz, mode='markers', marker=dict(size=8, color='rgba(255, 50, 50, 0.8)'), name='P_topo 湧升源'))
            cx = [c['pos'][0] for c in coldspots]; cy = [c['pos'][1] for c in coldspots]; cz = [c['pos'][2] for c in coldspots]
            t.append(go.Scatter3d(x=cx, y=cy, z=cz, mode='markers', marker=dict(size=8, color='rgba(50, 150, 255, 0.8)'), name='P_kin 沉降匯'))
            
            streams = self._calculate_htfc_streamlines('cmb_holographic', scale=sim_scale, point_density=600, extra_data=(hotspots, coldspots))
            t.extend(self._draw_batch_streamlines(streams, 'rgba(255, 204, 0, 0.5)', thickness=1.5))

        # Level 17: 全尺度無縫橋接
        elif level_idx == 16:
            sim_scale = 2500.0
            for key in self.landmarks.keys(): t.append(self._create_landmark_trace(key))
            streams = self._calculate_htfc_streamlines('bridged', scale=sim_scale, point_density=600)
            t.extend(self._draw_batch_streamlines(streams, 'rgba(0, 200, 255, 0.45)', thickness=1.5))

        # (若有需要可於此處補回 1~15 階的其他精簡渲染，此處著重展示核心實證)
        else:
            t.append(go.Scatter3d(x=[0], y=[0], z=[0], mode='text', text=["請切換至第 16 階或第 17 階觀測 HTFC 理論核心"], textfont=dict(color='white', size=20)))

        return t

    def get_render_html(self, requested_level_idx):
        fig = go.Figure()
        traces = self.build_level_traces(requested_level_idx)
        for trace in traces: fig.add_trace(trace)

        axis_config = dict(showgrid=True, gridcolor=self.grid_color, zeroline=False, showline=False, showbackground=False, showspikes=False, visible=True)
        fig.update_layout(
            title=f"<b>HTFC 物理觀測鏡: {self.levels[requested_level_idx]}</b>", 
            paper_bgcolor=self.bg_color, plot_bgcolor=self.bg_color, 
            scene=dict(bgcolor=self.bg_color, xaxis=axis_config, yaxis=axis_config, zaxis=axis_config, aspectmode='data'),
            hoverlabel=dict(bgcolor="black", font_color="yellow"), margin=dict(l=0, r=0, b=0, t=50)
        )
        return fig.to_html(include_plotlyjs=True, full_html=True)


class CosmicDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全像拓撲流體宇宙學 (HTFC) - 官方 3D 模擬引擎")
        self.setGeometry(50, 50, 1400, 900)
        self.colors = {'bg': '#02040A', 'grid': '#00FFFF', 'particle': '#C8C8C8', 'text': '#FFFF00'}
        self.opacities = {'bg': 95, 'grid': 15} 

        main_widget = QWidget(); self.setCentralWidget(main_widget); layout = QHBoxLayout(main_widget)

        control_panel = QFrame(); control_panel.setFixedWidth(300); control_panel.setStyleSheet("background-color: #1A1A24; color: #00FFFF; border-radius: 8px;")
        vbox = QVBoxLayout(control_panel)
        
        vbox.addWidget(QLabel("🌊 物理觀測尺度切換:"))
        self.level_combo = QComboBox()
        self.level_combo.setStyleSheet("background-color: #0A0A10; color: #00FFFF; padding: 5px; font-size: 13px; border: 1px solid #00FFFF;")
        temp_engine = HolographicFluidCosmologyEngine()
        self.level_combo.addItems(temp_engine.levels)
        self.level_combo.setCurrentIndex(16) # 預設開啟第 17 階 (Index 16)
        self.level_combo.currentIndexChanged.connect(self.update_render)
        vbox.addWidget(self.level_combo)

        self.btn_render = QPushButton("🚀 執行壓強矩陣運算")
        self.btn_render.setStyleSheet("background-color: #0066CC; color: white; font-weight: bold; padding: 15px; margin-top: 30px; border: 2px solid #00FFFF;")
        self.btn_render.clicked.connect(self.update_render)
        vbox.addWidget(self.btn_render)
        vbox.addStretch()

        self.browser = QWebEngineView()
        layout.addWidget(control_panel); layout.addWidget(self.browser)
        self.update_render()

    def update_render(self):
        self.btn_render.setText("⏳ HTFC 物理矩陣計算中...")
        QApplication.processEvents() 
        current_idx = self.level_combo.currentIndex()
        engine = HolographicFluidCosmologyEngine(bg_color=self.colors['bg'], grid_color=self.colors['grid'])
        html_content = engine.get_render_html(current_idx)
        
        temp_dir = tempfile.gettempdir(); temp_path = os.path.join(temp_dir, "htfc_engine.html")
        with open(temp_path, "w", encoding="utf-8") as f: f.write(html_content)
        self.browser.setUrl(QUrl.fromLocalFile(temp_path))
        self.btn_render.setText("🚀 執行壓強矩陣運算")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CosmicDesktopApp()
    window.show()
    sys.exit(app.exec())