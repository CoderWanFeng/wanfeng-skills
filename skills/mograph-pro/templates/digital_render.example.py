#!/usr/bin/env python3
"""接入任务级 Pillow 渲染器的分支模板，不是另一套全片引擎。

复制本模板和 scripts/digital_contract.py 到 mograph-task/src/。
传入本任务的 bg_layer、layer_registry、draw_head、draw_subtitles；
layer_registry 的函数必须真实绘制场景（img, scene, local_time -> img）。
开始 full 前调用 prepare；保留原有 ffmpeg 管道与响度交付流程。
"""
from digital_contract import validate_render_plan


def prepare(plan, layer_registry):
    if any(not callable(fn) for fn in layer_registry.values()):
        raise ValueError('注册表必须绑定真实绘图函数')
    return validate_render_plan(plan, implemented_layers=layer_registry, final=True)


def render_frame(frame_index, base_frame, plan, layer_registry, *, bg_layer, draw_head, draw_subtitles):
    fps = plan['meta'].get('fps', 30)
    # 与组装工具使用相同累计帧边界，避免毫秒量化造成边界闪帧。
    scene = next((s for s in plan['scenes']
                  if round(s['start'] * fps) <= frame_index < round(s['end'] * fps)), None)
    if scene is None:
        raise ValueError('数字人场景未覆盖当前帧')
    t = frame_index / fps
    local = max(0.0, t - scene['start'])
    if scene['mode'] == 'fs':
        image = bg_layer()  # 立即全屏覆盖，不让底片/占位背景参与淡入
    else:
        image = base_frame.copy()
    for name in scene.get('layers', []):
        image = layer_registry[name](image, scene, local)
    if scene['presenter'] == 'circle':
        image = draw_head(image, base_frame, scene)  # 裁切坐标须按新素材实测
    # B 段永远不调用 draw_head，也不从前一帧缓存人物层。
    return draw_subtitles(image, t, scene)
