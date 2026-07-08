#!/usr/bin/env bash
# smoke.sh — 端到端冒烟测试
# Usage: tests/smoke.sh
# 在 /tmp/pwb-smoke/ 跑所有 6 种类型创建 + build 验证

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_BASE="/tmp/pwb-smoke-$$"
LOG_DIR="$TEST_BASE/logs"

mkdir -p "$LOG_DIR"

PASS=0
FAIL=0
declare -a FAILED_TESTS

# 工具函数
ok() {
  echo "  ✅ $1"
  PASS=$((PASS+1))
}
fail() {
  echo "  ❌ $1"
  FAIL=$((FAIL+1))
  FAILED_TESTS+=("$1")
}

cleanup() {
  echo ""
  echo "🧹 清理测试目录: $TEST_BASE"
  rm -rf "$TEST_BASE"
}
trap cleanup EXIT

echo "🧪 冒烟测试: $SKILL_ROOT"
echo "📁 测试目录: $TEST_BASE"
echo ""

# Test 1: 路径校验
echo "📋 Test 1: 路径校验"
if "$SKILL_ROOT/scripts/validate-path.sh" /tmp/normal-path > /dev/null 2>&1; then
  ok "正常路径通过"
else
  fail "正常路径被拒"
fi
if "$SKILL_ROOT/scripts/validate-path.sh" "/System/test" > /dev/null 2>&1; then
  fail "系统目录未被拒"
else
  ok "系统目录被拒"
fi
if "$SKILL_ROOT/scripts/validate-path.sh" "/" > /dev/null 2>&1; then
  fail "根目录未被拒"
else
  ok "根目录被拒"
fi
if "$SKILL_ROOT/scripts/validate-path.sh" "~/Library/test" > /dev/null 2>&1; then
  fail "~/Library 未被拒"
else
  ok "~/Library 被拒"
fi

# Test 2: pick-dirname 加后缀（非空目录才加）
echo ""
echo "📋 Test 2: pick-dirname 加后缀"
# 把 TEST_BASE 也用 realpath 解析（macOS /tmp → /private/tmp）
if command -v realpath > /dev/null 2>&1; then
  TEST_BASE_REAL="$(realpath "$TEST_BASE")"
else
  TEST_BASE_REAL="$TEST_BASE"
fi
DIR1="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-pick")"
# 制造一个非空目录冲突
touch "$DIR1/somefile"
DIR2="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-pick")"
if [ "$DIR1" != "$DIR2" ] && [ "$DIR2" = "$TEST_BASE_REAL/test-pick-2" ]; then
  ok "非空冲突时加 -2 后缀: $(basename "$DIR2")"
else
  fail "未正确加 -2 后缀（DIR1=$DIR1, DIR2=$DIR2, 期望=$TEST_BASE_REAL/test-pick-2）"
fi
# 再制造冲突
touch "$DIR2/somefile"
DIR3="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-pick")"
if [ "$DIR3" = "$TEST_BASE_REAL/test-pick-3" ]; then
  ok "连续冲突时加 -3 后缀"
else
  fail "未加 -3 后缀（DIR3=$DIR3, 期望=$TEST_BASE_REAL/test-pick-3）"
fi
# 空目录应可复用：清空 DIR1 后再调用，应该返回 DIR1
rm -f "$DIR1/somefile"
DIR4="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-pick")"
if [ "$DIR4" = "$DIR1" ]; then
  ok "空目录可复用"
else
  fail "空目录未复用（应该是 $DIR1，得到 $DIR4）"
fi
rm -rf "$DIR1" "$DIR2" "$DIR3"

# Test 3: substitute 占位符替换
echo ""
echo "📋 Test 3: substitute 占位符替换"
TEST_FILE="$TEST_BASE/test.txt"
echo "Hello {{NAME}}, today is {{DATE_ISO}}" > "$TEST_FILE"
"$SKILL_ROOT/scripts/substitute.sh" --var "NAME=World" "$TEST_FILE"
if grep -q "Hello World" "$TEST_FILE" && grep -q "today is 20" "$TEST_FILE"; then
  ok "基本替换成功"
else
  fail "替换失败: $(cat $TEST_FILE)"
fi

# Test 4: substitute 条件删除
echo ""
echo "📋 Test 4: substitute 条件删除（空值删除整行）"
TEST_FILE="$TEST_BASE/test2.txt"
cat > "$TEST_FILE" <<EOF
line 1
{{GITHUB_OR_EMPTY}}{ icon: 'github', link: 'https://github.com/user' }
line 3
EOF
"$SKILL_ROOT/scripts/substitute.sh" --empty-line-delete "GITHUB_OR_EMPTY" "$TEST_FILE"
if ! grep -q "GITHUB_OR_EMPTY" "$TEST_FILE" && ! grep -q "github" "$TEST_FILE"; then
  ok "空值整行删除成功"
else
  fail "整行删除失败: $(cat $TEST_FILE)"
fi

# Test 5: substitute 检查未登记占位符
echo ""
echo "📋 Test 5: substitute 检查未登记占位符"
TEST_FILE="$TEST_BASE/test3.txt"
echo "{{UNKNOWN_VAR}}" > "$TEST_FILE"
if "$SKILL_ROOT/scripts/substitute.sh" --check "$TEST_FILE" > /dev/null 2>&1; then
  fail "未拒绝未登记的占位符"
else
  ok "拒绝未登记的占位符"
fi

# Test 6: Hexo 端到端
echo ""
echo "📋 Test 6: Hexo 端到端创建 + build"
HEXO_DIR="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-hexo")"
if "$SKILL_ROOT/scripts/init-hexo.sh" "$HEXO_DIR" "Smoke Test Blog" "Smoke test description" "Test Author" "testuser" > "$LOG_DIR/hexo-init.log" 2>&1; then
  ok "Hexo init 成功"
  if (cd "$HEXO_DIR" && npx hexo generate > "$LOG_DIR/hexo-build.log" 2>&1); then
    ok "Hexo build 成功"
    if [ -d "$HEXO_DIR/public" ] && [ -f "$HEXO_DIR/public/index.html" ]; then
      ok "Hexo 产物 public/index.html 存在"
    else
      fail "Hexo 产物缺失"
    fi
    if [ -d "$HEXO_DIR/public/2026" ]; then
      ok "Hexo 双语首篇用动态日期生成"
    else
      fail "Hexo 首篇未生成"
    fi
  else
    fail "Hexo build 失败（看 $LOG_DIR/hexo-build.log）"
  fi
else
  fail "Hexo init 失败（看 $LOG_DIR/hexo-init.log）"
fi

# Test 7: VitePress 端到端
echo ""
echo "📋 Test 7: VitePress 端到端创建 + build"
VP_DIR="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-vp")"
if "$SKILL_ROOT/scripts/init-vitepress.sh" "$VP_DIR" "Smoke Test KB" "Smoke test description" "Test Author" "testuser" > "$LOG_DIR/vp-init.log" 2>&1; then
  ok "VitePress init 成功"
  if (cd "$VP_DIR" && npx vitepress build docs > "$LOG_DIR/vp-build.log" 2>&1); then
    ok "VitePress build 成功"
    if [ -d "$VP_DIR/docs/.vitepress/dist" ] && [ -f "$VP_DIR/docs/.vitepress/dist/index.html" ]; then
      ok "VitePress 产物存在"
    else
      fail "VitePress 产物缺失"
    fi
  else
    fail "VitePress build 失败（看 $LOG_DIR/vp-build.log）"
  fi
else
  fail "VitePress init 失败（看 $LOG_DIR/vp-init.log）"
fi

# Test 8: Vue 3 端到端
echo ""
echo "📋 Test 8: Vue 3 端到端创建 + build"
VUE_DIR="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-vue")"
if "$SKILL_ROOT/scripts/init-vue3.sh" "$VUE_DIR" "Smoke Test Tools" "Smoke test description" "Test Author" "testuser" > "$LOG_DIR/vue-init.log" 2>&1; then
  ok "Vue 3 init 成功"
  if (cd "$VUE_DIR" && npm run build > "$LOG_DIR/vue-build.log" 2>&1); then
    ok "Vue 3 build 成功"
    if [ -d "$VUE_DIR/dist" ] && [ -f "$VUE_DIR/dist/index.html" ]; then
      ok "Vue 3 产物存在"
    else
      fail "Vue 3 产物缺失"
    fi
  else
    fail "Vue 3 build 失败（看 $LOG_DIR/vue-build.log）"
  fi
else
  fail "Vue 3 init 失败（看 $LOG_DIR/vue-init.log）"
fi

# Test 9: Portfolio 端到端
echo ""
echo "📋 Test 9: Portfolio 端到端"
PORT_DIR="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-port")"
if "$SKILL_ROOT/scripts/init-portfolio.sh" "$PORT_DIR" "Smoke Portfolio" "Smoke description" "Test Author" "testuser" > "$LOG_DIR/port-init.log" 2>&1; then
  ok "Portfolio init 成功"
  if [ -f "$PORT_DIR/index.html" ] && [ -f "$PORT_DIR/style.css" ]; then
    ok "Portfolio 文件存在"
  else
    fail "Portfolio 文件缺失"
  fi
  if grep -q "Smoke Portfolio" "$PORT_DIR/index.html"; then
    ok "Portfolio 占位符替换成功"
  else
    fail "Portfolio 占位符未替换"
  fi
else
  fail "Portfolio init 失败（看 $LOG_DIR/port-init.log）"
fi

# Test 10: Resume 端到端
echo ""
echo "📋 Test 10: Resume 端到端"
RES_DIR="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-res")"
if "$SKILL_ROOT/scripts/init-resume.sh" "$RES_DIR" "Smoke Resume" "Smoke description" "Test Author" "testuser" > "$LOG_DIR/res-init.log" 2>&1; then
  ok "Resume init 成功"
  if [ -f "$RES_DIR/index.html" ]; then
    ok "Resume 文件存在"
  else
    fail "Resume 文件缺失"
  fi
else
  fail "Resume init 失败（看 $LOG_DIR/res-init.log）"
fi

# Test 11: GitHub 用户名留空
echo ""
echo "📋 Test 11: GitHub 用户名留空测试"
EMPTY_DIR="$("$SKILL_ROOT/scripts/pick-dirname.sh" "$TEST_BASE" "test-empty-gh")"
if "$SKILL_ROOT/scripts/init-portfolio.sh" "$EMPTY_DIR" "Test" "Test" "Test Author" "" > "$LOG_DIR/empty-gh.log" 2>&1; then
  if ! grep -q "GITHUB_OR_EMPTY" "$EMPTY_DIR/index.html"; then
    ok "留空 GitHub 用户名时 socialLinks 行被删除"
  else
    fail "留空时未删除"
  fi
else
  fail "留空 GitHub 场景 init 失败"
fi

# Test 12: detect-deploy-tools 输出有效 JSON
echo ""
echo "📋 Test 12: detect-deploy-tools 输出有效 JSON"
DETECT_OUT="$("$SKILL_ROOT/scripts/detect-deploy-tools.sh" 2>&1)"
if echo "$DETECT_OUT" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'platforms' in d and 'recommended' in d" 2>/dev/null; then
  ok "detect-deploy-tools 输出有效 JSON"
else
  fail "detect-deploy-tools JSON 格式错: $DETECT_OUT"
fi

# Test 13: verify-deploy.sh 验证 200 站点
echo ""
echo "📋 Test 13: verify-deploy.sh 验证 HTTP 200 站点"
HTTP_PID_FILE="$TEST_BASE/http.pid"
python3 -c "
import http.server, socketserver, threading
import os
os.chdir('$TEST_BASE')
handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(('', 18888), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
import time
time.sleep(60)
" > /dev/null 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > "$HTTP_PID_FILE"
sleep 2
if "$SKILL_ROOT/scripts/verify-deploy.sh" "http://localhost:18888" "" 15 > "$LOG_DIR/verify.log" 2>&1; then
  if grep -q "HTTP 200" "$LOG_DIR/verify.log" || grep -q "部署验证通过" "$LOG_DIR/verify.log"; then
    ok "verify-deploy 识别 200 站点"
  else
    fail "verify-deploy 200 站点输出异常: $(cat $LOG_DIR/verify.log)"
  fi
else
  fail "verify-deploy 200 站点失败: $(cat $LOG_DIR/verify.log)"
fi
kill $HTTP_PID 2>/dev/null
rm -f "$HTTP_PID_FILE"

# Test 14: optimize-images.sh 在没 sharp 时优雅降级
echo ""
echo "📋 Test 14: optimize-images 优雅降级（无 sharp）"
TEST_IMG_DIR="$TEST_BASE/test-img"
mkdir -p "$TEST_IMG_DIR"
# 创建一个假的"项目"结构
mkdir -p "$TEST_IMG_DIR/project"
echo '{}' > "$TEST_IMG_DIR/project/package.json"
mkdir -p "$TEST_IMG_DIR/project/dist"
echo "fake" > "$TEST_IMG_DIR/project/dist/index.html"
if "$SKILL_ROOT/scripts/optimize-images.sh" "$TEST_IMG_DIR/project/dist" > "$LOG_DIR/opt.log" 2>&1; then
  if grep -q "未找到 sharp" "$LOG_DIR/opt.log"; then
    ok "optimize-images 优雅降级（提示未找到 sharp）"
  else
    ok "optimize-images 完成（找到图片则压缩，否则跳过）"
  fi
else
  fail "optimize-images 报错（应优雅降级）"
fi

# Test 15: optimize-all.sh 在没 dist 时跳过
echo ""
echo "📋 Test 15: optimize-all 在没 dist 时跳过"
TEST_EMPTY_DIR="$TEST_BASE/empty-test"
mkdir -p "$TEST_EMPTY_DIR"
if "$SKILL_ROOT/scripts/optimize-all.sh" hexo "$TEST_EMPTY_DIR" > "$LOG_DIR/empty-opt.log" 2>&1; then
  if grep -q "dist 目录不存在" "$LOG_DIR/empty-opt.log"; then
    ok "optimize-all 在没 dist 时优雅跳过"
  else
    fail "optimize-all 没正确跳过: $(cat $LOG_DIR/empty-opt.log)"
  fi
else
  fail "optimize-all 在没 dist 时报错"
fi

# Test 16: deploy.sh 帮助信息
echo ""
echo "📋 Test 16: deploy.sh 缺少参数时报错"
if "$SKILL_ROOT/scripts/deploy.sh" > /dev/null 2>&1; then
  fail "deploy.sh 缺参数应报错"
else
  ok "deploy.sh 缺参数正确报错"
fi

# Test 17: deploy.sh 缺 dist 时报错
echo ""
echo "📋 Test 17: deploy.sh 缺 dist 目录时优雅报错"
if "$SKILL_ROOT/scripts/deploy.sh" hexo /tmp/nonexistent-path-xyz > /dev/null 2>&1; then
  fail "deploy.sh 缺 dist 应报错"
else
  ok "deploy.sh 缺 dist 优雅报错"
fi

# Test 18: deploy.sh --no-verify 跳过验证
echo ""
echo "📋 Test 18: deploy.sh --no-verify + --no-optimize 不调用实际部署"
# 这个测试不实际部署（避免网络），只检查参数解析
DEPLOY_OUT="$("$SKILL_ROOT/scripts/deploy.sh" --help 2>&1 || true)"
if echo "$DEPLOY_OUT" | grep -q "platform\|dist\|optimize"; then
  ok "deploy.sh --help 输出选项说明"
else
  # 不强制要求 --help，但检查 usage 格式
  DEPLOY_OUT2="$("$SKILL_ROOT/scripts/deploy.sh" 2>&1 || true)"
  if echo "$DEPLOY_OUT2" | grep -q "Usage"; then
    ok "deploy.sh 缺参数输出 Usage"
  else
    fail "deploy.sh 缺参数输出异常: $DEPLOY_OUT2"
  fi
fi

echo ""
echo "═══════════════════════════════════════"
echo "📊 测试结果"
echo "═══════════════════════════════════════"
echo "✅ 通过: $PASS"
echo "❌ 失败: $FAIL"
if [ $FAIL -gt 0 ]; then
  echo ""
  echo "失败的测试:"
  for t in "${FAILED_TESTS[@]}"; do
    echo "  - $t"
  done
  exit 1
else
  echo ""
  echo "🎉 所有测试通过！"
  exit 0
fi