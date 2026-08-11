# Build-quality tasks for technobasant.github.io.
#
# html-proofer is driven through the Ruby API rather than the CLI: the CLI flag
# names churn between majors (`--disable-external` vs `--disable_external`,
# `--url-swap` vs `--swap-urls`, ...), while the option hash keys are stable.
#
#   rake check           internal links, images, scripts, OpenGraph  (CI gate)
#   rake check:external  adds off-site link checking                 (weekly cron)
#   rake verify          output assertions against _site
#   rake jsonld          every ld+json block in _site must parse

require "html-proofer"
require "json"
require "nokogiri"
require "shellwords"
require "yaml"
require "date"
require "open3"

SITE_DIR = "./_site".freeze

BASE = {
  allow_hash_href: true,
  enforce_https: false,
  check_internal_hash: true,
  checks: %w[Links Images Scripts OpenGraph],
  swap_urls: { %r{^https://technobasant\.github\.io} => "" },
  ignore_urls: [%r{^mailto:}]
}.freeze

def site_built!
  return true if Dir.exist?(SITE_DIR)

  abort "_site/ not found — run `make build` (or `bundle exec jekyll build`) first."
end

desc "Check the built site: internal links, images, scripts, OpenGraph"
task :check do
  site_built!
  HTMLProofer.check_directory(SITE_DIR, BASE.merge(disable_external: true)).run
end

namespace :check do
  desc "Check external links too (slow, network-bound — weekly cron, never a deploy gate)"
  task :external do
    site_built!
    HTMLProofer.check_directory(SITE_DIR, BASE.merge(
      disable_external: false,
      typhoeus: { timeout: 20, ssl_verifypeer: true },
      hydra: { max_concurrency: 10 },
      ignore_status_codes: [403, 429],
      # LinkedIn serves a 999/challenge page to anything that is not a browser.
      ignore_urls: BASE[:ignore_urls] + [%r{^https://www\.linkedin\.com}]
    )).run
  end
end

desc "Every <script type=\"application/ld+json\"> block in _site must parse"
task :jsonld do
  site_built!

  pattern = %r{<script[^>]*type=(["'])application/ld\+json\1[^>]*>(.*?)</script>}mi
  blocks = 0
  failures = []

  Dir.glob("#{SITE_DIR}/**/*.html").sort.each do |path|
    File.read(path).scan(pattern) do |_quote, body|
      blocks += 1
      begin
        parsed = JSON.parse(body)
        if parsed.is_a?(Hash) && !parsed.key?("@context")
          failures << "#{path}: ld+json block has no @context"
        end
      rescue JSON::ParserError => e
        failures << "#{path}: #{e.message.lines.first.to_s.strip}"
      end
    end
  end

  if failures.any?
    failures.each { |f| warn "  FAIL  #{f}" }
    abort "jsonld: #{failures.size} of #{blocks} block(s) failed to parse"
  end

  if blocks.zero?
    puts "jsonld: SKIP — no ld+json blocks in _site yet"
  else
    puts "jsonld: ok — #{blocks} block(s) parsed"
  end
end

# ── rake content ───────────────────────────────────────────────────────────
# Editorial contracts for published writing. Drafts are intentionally excluded:
# they may be outlines, while everything under _posts/ must be reader-ready.

desc "Validate published post metadata, structure and tutorial contracts"
task :content do
  failures = []
  posts = Dir.glob("_posts/*.{md,markdown}").sort

  posts.each do |path|
    raw = File.read(path)
    match = raw.match(/\A---\s*\n(.*?)\n---\s*\n/m)
    unless match
      failures << "#{path}: missing YAML front matter"
      next
    end

    begin
      data = YAML.safe_load(
        match[1],
        permitted_classes: [Date, Time],
        aliases: true
      ) || {}
    rescue Psych::SyntaxError => e
      failures << "#{path}: invalid YAML — #{e.message.lines.first.to_s.strip}"
      next
    end

    body = raw[match.end(0)..].to_s
    prose_body = body.gsub(/```.*?```/m, " ")
    type = data["type"].to_s

    in_fence = false
    opening_fences = 0
    body.each_line.with_index(1) do |line, line_number|
      next unless line.start_with?("```")

      if in_fence
        in_fence = false
      else
        opening_fences += 1
        language = line.delete_prefix("```").strip
        if language.empty?
          failures << "#{path}:#{line_number}: fenced code blocks need a language identifier"
        end
        in_fence = true
      end
    end
    failures << "#{path}: unclosed fenced code block" if in_fence

    %w[title description date type tags key_takeaways].each do |key|
      value = data[key]
      empty = value.nil? || (value.respond_to?(:empty?) && value.empty?)
      failures << "#{path}: #{key} is required" if empty
    end

    description = data["description"].to_s
    unless description.empty? || (120..165).cover?(description.length)
      failures << "#{path}: description must be 120–165 characters (got #{description.length})"
    end

    failures << "#{path}: type must be essay, tutorial or note" unless %w[essay tutorial note].include?(type)

    tags = data["tags"]
    unless tags.is_a?(Array) && (1..3).cover?(tags.size)
      failures << "#{path}: tags must contain 1–3 slugs"
    end

    takeaways = data["key_takeaways"]
    unless takeaways.is_a?(Array) && (3..5).cover?(takeaways.size) && takeaways.all? { |item| item.to_s.length >= 35 }
      failures << "#{path}: key_takeaways must contain 3–5 complete, useful statements"
    end

    if prose_body.match?(/^#\s+/)
      failures << "#{path}: do not author an H1; the layout renders page.title"
    end

    h2_count = prose_body.scan(/^##\s+/).size
    minimum_h2 = type == "tutorial" ? 4 : 3
    failures << "#{path}: needs at least #{minimum_h2} H2 sections (got #{h2_count})" if h2_count < minimum_h2

    prose_words = prose_body
      .gsub(/<[^>]+>/, " ")
      .scan(/[[:alpha:]][[:alnum:]'’-]*/)
      .size
    minimum_words = { "tutorial" => 900, "essay" => 650, "note" => 250 }.fetch(type, 250)
    failures << "#{path}: body is too slight for a finished #{type} (#{prose_words}/#{minimum_words} prose words)" if prose_words < minimum_words

    if body.match?(/\bthe draft (?:will|argues|covers)\b/i)
      failures << "#{path}: contains outline language instead of finished copy"
    end
    failures << "#{path}: links must use /work/, not the retired /projects/ route" if body.include?("/projects/")

    verify_count = body.scan(/^\*\*Verify\.\*\*/).size
    styled_verify_count = body.scan(/^\{:\s*\.verify\s*\}$/).size
    if verify_count != styled_verify_count
      failures << "#{path}: every Verify checkpoint needs a following {: .verify} marker"
    end

    if type == "tutorial"
      %w[level time_estimate what_youll_build prerequisites tested_on].each do |key|
        value = data[key]
        empty = value.nil? || (value.respond_to?(:empty?) && value.empty?)
        failures << "#{path}: tutorial field #{key} is required" if empty
      end
      unless %w[beginner intermediate advanced].include?(data["level"].to_s)
        failures << "#{path}: tutorial level must be beginner, intermediate or advanced"
      end
      prereqs = data["prerequisites"]
      failures << "#{path}: tutorials need at least two prerequisites" unless prereqs.is_a?(Array) && prereqs.size >= 2
      failures << "#{path}: tutorials need at least one reproducible code or console block" if opening_fences.zero?
    end

    puts "  ok    #{File.basename(path)} — #{type}, #{prose_words} prose words, #{h2_count} sections"
  end

  if failures.any?
    failures.each { |failure| warn "  FAIL  #{failure}" }
    abort "content: #{failures.size} editorial contract failure(s)"
  end

  puts "content: ok — #{posts.size} published post(s)"
end

# ── rake privacy ────────────────────────────────────────────────────────────
# Current-tree guardrails for public material. Employer names, role history, and
# the professional metrics explicitly approved in `_data/metrics.yml` are
# allowed. Internal platform names, customer-derived counts, runtime topology,
# and retired private routes remain blocked everywhere.
#
# CONFIDENTIAL — withheld everywhere. Internal platform names, runtime topology,
# customer-derived counts and internal scale descriptions are the employer's,
# not general skill and knowledge.
CONFIDENTIAL_PATTERNS = {
  "legacy employer case-study route" => %r{/work/(?:uxcam-data-platform|iceberg-lakehouse-scd|app-analytics-agent-platform|serving-layer-100m-queries)/}i,
  "internal platform name" => /App Analytics Agent Platform/i,
  "runtime topology" => /self-managed (?:Spark|Kubernetes)/i,
  "internal scale description" => /multi[- ]petabyte|petabyte[- ]scale/i,
  "customer-derived count" => /25,?000\+?\s*(?:mobile\s*)?apps?|500\+?\s*(?:mobile\s*)?apps?/i
}.freeze

SENSITIVE_PUBLIC_PATTERNS = CONFIDENTIAL_PATTERNS.freeze

APPROVED_PROFESSIONAL_METRICS = %w[
  experience
  professional_platform_scale
  professional_event_volume
  professional_uptime
  professional_cost_reduction
  professional_processing_improvement
  professional_analytics_delivery
  professional_manual_effort
  professional_team_delivery
  professional_mentoring
  professional_daily_processing
  professional_query_volume
  professional_query_latency
  professional_project_team
  professional_project_delivery
  professional_backend_users
  professional_test_coverage
].freeze

PUBLIC_SOURCE_GLOBS = %w[
  _posts/**/*.{md,markdown,html}
  _pages/**/*.{md,markdown,html}
  _work/**/*.{md,markdown,html}
  _data/**/*.{yml,yaml,json}
  _includes/**/*.{html,md}
  _layouts/**/*.{html,md}
  _config.yml
  index.md
  llms.txt
].freeze

def privacy_findings(path, body, patterns = SENSITIVE_PUBLIC_PATTERNS)
  patterns.filter_map do |label, pattern|
    match = body.match(pattern)
    next unless match

    line = body[0...match.begin(0)].count("\n") + 1
    "#{path}:#{line}: #{label} — #{match[0].inspect}"
  end
end

desc "Enforce the approved evidence boundary and reject confidential employer details"
task :privacy do
  failures = []

  PUBLIC_SOURCE_GLOBS.flat_map { |glob| Dir.glob(glob) }.uniq.sort.each do |path|
    next unless File.file?(path)
    failures.concat(privacy_findings(path, File.read(path)))
  end

  if Dir.exist?(SITE_DIR)
    Dir.glob("#{SITE_DIR}/**/*.{html,txt,xml,json}").sort.each do |path|
      failures.concat(privacy_findings(path, File.read(path)))
    end
  end

  metrics_path = "_data/metrics.yml"
  if File.exist?(metrics_path)
    metrics = YAML.safe_load_file(metrics_path, permitted_classes: [Date]) || {}
    professional = metrics.select { |_key, metric| metric["scope"] == "professional" }

    unexpected = professional.keys - APPROVED_PROFESSIONAL_METRICS
    unexpected.each do |key|
      failures << "#{metrics_path}: unapproved professional metric key — #{key.inspect}"
    end

    APPROVED_PROFESSIONAL_METRICS.each do |key|
      metric = metrics[key]
      if metric.nil?
        failures << "#{metrics_path}: approved professional metric is missing — #{key.inspect}"
        next
      end

      %w[value label method source context].each do |field|
        failures << "#{metrics_path}: #{key}.#{field} is required" if metric[field].to_s.strip.empty?
      end
    end
  end

  # The generator and PDF share the site's public evidence boundary. Exact
  # professional figures are governed by the metrics allowlist above; the
  # confidential patterns still reject internal names, topology, and
  # customer-derived counts.
  resume_src = "scripts/generate-resume-pdf.py"
  if File.exist?(resume_src)
    failures.concat(privacy_findings(resume_src, File.read(resume_src), CONFIDENTIAL_PATTERNS))
  end

  resume_pdf = "assets/basant-bhattarai-resume.pdf"
  if File.exist?(resume_pdf)
    if system("command -v pdftotext >/dev/null 2>&1")
      text, status = Open3.capture2("pdftotext", resume_pdf, "-")
      if status.success?
        failures.concat(privacy_findings(resume_pdf, text, CONFIDENTIAL_PATTERNS))
      else
        failures << "#{resume_pdf}: pdftotext could not inspect the public résumé"
      end
    else
      warn "privacy: pdftotext unavailable; PDF text inspection skipped"
    end
  end

  if failures.any?
    failures.each { |failure| warn "  FAIL  #{failure}" }
    abort "privacy: #{failures.size} public disclosure guardrail failure(s)"
  end

  puts "privacy: ok — public source, built text, and available PDF text are clean"
end

# ── rake verify ────────────────────────────────────────────────────────────
# Output assertions. Deliberately tolerant: this repo is built by several people
# at once, so a file that does not exist yet is a SKIP, not a crash. Only a file
# that exists and is *wrong* fails the task.

class Verifier
  def initialize
    @pass = 0
    @skip = 0
    @fail = []
  end

  def ok(msg)
    @pass += 1
    puts "  ok    #{msg}"
  end

  def skip(msg)
    @skip += 1
    puts "  skip  #{msg}"
  end

  def bad(msg)
    @fail << msg
    puts "  FAIL  #{msg}"
  end

  # Runs the block only when every path exists; otherwise reports a skip.
  def with(*paths, label:)
    missing = paths.reject { |p| File.exist?(p) }
    return skip("#{label} — not generated yet (#{missing.map { |m| File.basename(m) }.join(', ')})") if missing.any?

    yield
  end

  def sh?(cmd)
    system(cmd, out: File::NULL, err: File::NULL)
  end

  def report!
    puts
    puts "verify: #{@pass} passed, #{@skip} skipped, #{@fail.size} failed"
    abort "verify failed" if @fail.any?
  end
end

desc "Assert the shape of the built output (feed, sitemap, canonical, cards, robots)"
task :verify do
  site_built!
  v = Verifier.new

  feed_xml  = "#{SITE_DIR}/writing/feed.xml"
  feed_json = "#{SITE_DIR}/writing/feed.json"
  sitemap   = "#{SITE_DIR}/sitemap.xml"
  index     = "#{SITE_DIR}/index.html"
  robots    = "#{SITE_DIR}/robots.txt"

  v.with(feed_xml, label: "atom feed exists at /writing/feed.xml") do
    v.ok "atom feed exists at /writing/feed.xml"
  end

  [feed_xml, sitemap].each do |f|
    v.with(f, label: "#{File.basename(f)} is well-formed XML") do
      if v.sh?("xmllint --noout #{Shellwords.escape(f)}")
        v.ok "#{File.basename(f)} is well-formed XML"
      else
        v.bad "#{File.basename(f)} is not well-formed XML"
      end
    end
  end

  v.with(sitemap, label: "sitemap lists /writing/ URLs") do
    body = File.read(sitemap)
    if body.include?("<loc>https://technobasant.github.io/writing/")
      v.ok "sitemap lists /writing/ URLs"
    else
      v.bad "sitemap has no <loc>https://technobasant.github.io/writing/ entry"
    end

    if body.include?("404.html")
      v.bad "sitemap contains 404.html (set `sitemap: false` in its front matter)"
    else
      v.ok "sitemap excludes 404.html"
    end
  end

  v.with(index, label: "home page head tags") do
    body = File.read(index)
    if body.include?('rel="canonical"')
      v.ok "index.html has rel=\"canonical\""
    else
      v.bad "index.html is missing rel=\"canonical\""
    end

    if body.include?('twitter:card" content="summary_large_image"')
      v.ok "index.html has twitter:card=summary_large_image"
    else
      v.bad "index.html is missing twitter:card=summary_large_image"
    end
  end

  v.with(feed_json, label: "/writing/feed.json is valid JSON") do
    begin
      JSON.parse(File.read(feed_json))
      v.ok "/writing/feed.json is valid JSON"
    rescue JSON::ParserError => e
      v.bad "/writing/feed.json does not parse: #{e.message.lines.first.to_s.strip}"
    end
  end

  v.with(robots, label: "robots.txt points at an absolute sitemap") do
    if File.read(robots).match?(/^\s*Sitemap:\s*https:\/\//i)
      v.ok "robots.txt points at an absolute sitemap"
    else
      v.bad "robots.txt has no `Sitemap: https://…` line"
    end
  end

  card_pages = %w[index.html writing/index.html work/index.html]
    .map { |path| File.join(SITE_DIR, path) }
  v.with(*card_pages, label: "cards are native whole-card links with visible affordances") do
    failures = []
    card_count = 0

    card_pages.each do |path|
      doc = Nokogiri::HTML(File.read(path))
      doc.css(".post-card, .case-card").each do |card|
        card_count += 1
        links = card.css("a[href]")
        affordance = card.at_css(".post-card__open, .case-card__open")
        failures << "#{path}: card has #{links.size} links" unless links.size == 1
        failures << "#{path}: card has no read/open affordance" unless affordance
      end
    end

    home_doc = Nokogiri::HTML(File.read(File.join(SITE_DIR, "index.html")))
    home_doc.css("a.focus[href]").each do |card|
      card_count += 1
      failures << "index.html: focus card has no explore affordance" unless card.at_css(".focus-open")
    end

    writing_doc = Nokogiri::HTML(File.read(File.join(SITE_DIR, "writing/index.html")))
    feature = writing_doc.at_css("a.writing-feature__link[href] h2")
    failures << "writing index: lead story is not one native linked feature" unless feature

    if failures.empty? && card_count.positive?
      v.ok "#{card_count} cards and the lead story use native links with clear affordances"
    else
      failures.each { |failure| v.bad(failure) }
    end
  end

  # Assets this task's owner generated — these must always be present.
  {
    "assets/apple-touch-icon.png" => 180,
    "assets/og/og-default-v3.png" => nil
  }.each_key do |asset|
    built = File.join(SITE_DIR, asset)
    v.with(built, label: "#{asset} shipped to _site") do
      v.ok "#{asset} shipped to _site (#{File.size(built)} B)"
    end
  end

  v.report!
end

# ─────────────────────────────────────────────────────────────────────────────
# TOKEN CONTRAST
#
# Two bugs motivated this task, both the same shape: a colour was measured
# against ONE background, shipped, and then failed on a raised panel that a
# component was free to place it on. Dark --ink-3 passed 5.23:1 on --surface-0
# and failed 4.39:1 on a panel; light --ink-3 passed 4.94:1 on --surface-0 and
# failed 4.45:1 on --surface-2 and 4.00:1 on --surface-3.
#
# axe cannot catch this class reliably, because it only sees the combinations
# that happen to exist in today's markup — light --surface-3 had no --ink-3 text
# on it, so the 4.00:1 pair was invisible to it. A component added later would
# have shipped the failure silently. This checks the token matrix instead of the
# rendered sample: every general-purpose text token against every surface it is
# permitted to land on, in both themes.
# ─────────────────────────────────────────────────────────────────────────────
TOKENS_FILE = "_sass/_tokens.scss".freeze

# Any surface a component may set as a background. A text token has to clear
# AA on all of them, not on whichever one it was first sampled against.
SURFACES = %w[surface-0 surface-1 surface-2 surface-3].freeze

# 4.5:1 — body-weight text tokens used freely across surfaces.
TEXT_TOKENS = %w[ink-1 ink-2 ink-3 accent accent-hi].freeze

# Tokens that are NOT free to land anywhere: each is checked only against the
# backgrounds it is actually painted on. Pairing them against all four surfaces
# would be a false failure, and a gate that cries wolf gets switched off.
#   code-meta      .code-lang, only ever inside .highlighter-rouge
#   accent-on      solid brass fills — .btn--primary and .skip-link. Note this
#                  is --accent-fill, NOT --accent: in light mode --accent is
#                  brass darkened for text weight and is not a fill.
SCOPED_PAIRS = [
  ["code-meta",      "code-bg",        4.5],
  ["code-meta",      "code-header-bg", 4.5],
  ["accent-on",      "accent-fill",    4.5],
  ["sel-fg",         "sel-bg",         4.5],
  ["code-fg-inline", "code-bg",        4.5],
  ["sx-fg",          "code-bg",        4.5],
  ["sx-out",         "code-bg",        4.5]
].freeze

# 3:1 — WCAG 1.4.11. A border that is a control's only affordance, and the
# focus ring, are non-text contrast, not text.
NONTEXT_TOKENS = %w[focus line-control].freeze

def parse_theme_tokens(body, from_line, to_line)
  body.lines[from_line...to_line].each_with_object({}) do |line, acc|
    next unless (m = line.match(/^\s*--([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))\s*;/))

    acc[m[1]] = m[2].strip
  end
end

def srgb_to_linear(channel)
  c = channel / 255.0
  c <= 0.04045 ? c / 12.92 : (((c + 0.055) / 1.055)**2.4)
end

def parse_color(value)
  if (m = value.match(/^#([0-9a-fA-F]{6})$/))
    [m[1][0, 2].to_i(16), m[1][2, 2].to_i(16), m[1][4, 2].to_i(16), 1.0]
  elsif (m = value.match(/^#([0-9a-fA-F]{3})$/))
    m[1].chars.map { |c| (c * 2).to_i(16) } + [1.0]
  elsif (m = value.match(%r{^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?\s*\)$}))
    [m[1].to_f.round, m[2].to_f.round, m[3].to_f.round, (m[4] || 1).to_f]
  end
end

def composite(fg, bg)
  a = fg[3]
  (0..2).map { |i| (a * fg[i] + (1 - a) * bg[i]).round } + [1.0]
end

def luminance(rgb)
  0.2126 * srgb_to_linear(rgb[0]) +
    0.7152 * srgb_to_linear(rgb[1]) +
    0.0722 * srgb_to_linear(rgb[2])
end

def contrast(fg, bg)
  fg = composite(fg, bg) if fg[3] < 1.0
  a = luminance(fg)
  b = luminance(bg)
  a, b = b, a if b > a
  (a + 0.05) / (b + 0.05)
end

desc "Every text token must clear AA on every surface it can land on, both themes"
task :tokens do
  abort "tokens: #{TOKENS_FILE} not found" unless File.exist?(TOKENS_FILE)

  body   = File.read(TOKENS_FILE)
  lines  = body.lines
  dark_i  = lines.index { |l| l.include?('[data-theme="dark"]') }
  light_i = lines.index { |l| l.include?('[data-theme="light"]') }
  abort "tokens: could not locate the dark and light blocks" unless dark_i && light_i

  base   = parse_theme_tokens(body, 0, dark_i)
  themes = {
    "dark"  => base.merge(parse_theme_tokens(body, dark_i, light_i)),
    "light" => base.merge(parse_theme_tokens(body, light_i, lines.length))
  }

  failures = []
  checked  = 0

  themes.each do |theme, tok|
    pairs = TEXT_TOKENS.product(SURFACES).map { |f, b| [f, b, 4.5] } +
            NONTEXT_TOKENS.product(SURFACES).map { |f, b| [f, b, 3.0] } +
            SCOPED_PAIRS

    pairs.each do |fg_name, bg_name, floor|
      fg_raw = tok[fg_name]
      bg_raw = tok[bg_name]
      next unless fg_raw && bg_raw

      fg = parse_color(fg_raw)
      bg = parse_color(bg_raw)
      next unless fg && bg

      checked += 1
      ratio = contrast(fg, bg)
      next if ratio >= floor

      failures << format("%-5s --%-15s on --%-10s %.2f:1 (needs %.1f:1)",
                         theme, fg_name, bg_name, ratio, floor)
    end
  end

  if failures.empty?
    puts "tokens: ok — #{checked} token pair(s) clear AA across both themes"
  else
    warn "tokens: #{failures.length} failing pair(s)"
    failures.each { |f| warn "  #{f}" }
    abort "tokens: FAILED"
  end
end

task default: %i[content privacy check verify jsonld tokens]
