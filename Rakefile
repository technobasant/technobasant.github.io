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
require "tmpdir"
require "json"
require "nokogiri"
require "yaml"
require "date"
require "open3"

SITE_DIR = "./_site".freeze

SITE_URL = begin
  config = YAML.safe_load_file("_config.yml", permitted_classes: [Date, Time]) || {}
  url = config["url"].to_s.strip.sub(%r{/\z}, "")
  abort "Rakefile: _config.yml is missing `url`" if url.empty?
  url
end.freeze

# html-proofer treats absolute site URLs as external unless they are swapped
# back to local paths. Keep the retired GitHub Pages host so leftover links
# still get checked internally after the custom domain lands.
SITE_URL_SWAP = %r{^(?:#{Regexp.escape(SITE_URL)}|https://technobasant\.github\.io)}

BASE = {
  allow_hash_href: true,
  enforce_https: false,
  check_internal_hash: true,
  checks: %w[Links Images Scripts OpenGraph],
  swap_urls: { SITE_URL_SWAP => "" },
  ignore_urls: [%r{^mailto:}]
}.freeze

# Sources that, if newer than the build, mean the audit is looking at a page
# that no longer exists in the form it is about to bless.
STALENESS_GLOBS = %w[
  _posts/**/*.md _work/**/*.md _pages/**/*.md _layouts/**/*.html
  _includes/**/*.html _data/**/*.yml _sass/**/*.scss assets/**/*.{scss,js}
  index.md _config.yml
].freeze

def site_built!
  abort "_site/ not found — run `make build` (or `bundle exec jekyll build`) first." unless Dir.exist?(SITE_DIR)

  # Nothing here builds the site; every task audits whatever `_site` happens to
  # contain. That is fine until a build *fails* — then the previous `_site`
  # survives, the whole suite passes against it, and the run reports green for a
  # site that cannot be generated. That happened: a `{% macro %}` inside a code
  # fence made Jekyll abort with a Liquid syntax error, and `rake default` went
  # on to pass 12/12 against the last good output.
  built = File.mtime(File.join(SITE_DIR, "index.html")) if File.exist?(File.join(SITE_DIR, "index.html"))
  return true unless built

  newer = STALENESS_GLOBS.flat_map { |g| Dir.glob(g) }.select { |f| File.mtime(f) > built }
  return true if newer.empty?

  abort <<~MSG
    _site/ is older than #{newer.size} source file(s) — the audit would pass on stale output.
      #{newer.sort_by { |f| -File.mtime(f).to_i }.first(5).join("\n  ")}
    Rebuild first:  JEKYLL_ENV=production bundle exec jekyll build
  MSG
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

    cover = data["cover"]
    unless cover.is_a?(Hash) && cover["base"].to_s.start_with?("/assets/") && cover["alt"].to_s.length >= 24
      failures << "#{path}: cover is required (base under /assets/, alt ≥ 24 characters)"
    end
    if cover.is_a?(Hash) && cover["base"].to_s != ""
      fallback = cover["fallback_width"] || "1600"
      raster = "#{cover['base'].delete_prefix('/')}-#{fallback}.jpg"
      failures << "#{path}: cover raster missing (#{raster})" unless File.exist?(raster)
    end

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
      begin
        Nokogiri::XML(File.read(f)) { |config| config.strict }
        v.ok "#{File.basename(f)} is well-formed XML"
      rescue Nokogiri::XML::SyntaxError => e
        v.bad "#{File.basename(f)} is not well-formed XML: #{e.message.lines.first.to_s.strip}"
      end
    end
  end

  v.with(sitemap, label: "sitemap lists /writing/ URLs") do
    body = File.read(sitemap)
    writing_loc = "<loc>#{SITE_URL}/writing/"
    if body.include?(writing_loc)
      v.ok "sitemap lists /writing/ URLs"
    else
      v.bad "sitemap has no #{writing_loc} entry"
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
    writing_cards = writing_doc.css(".writing-feed .post-card")
    linked_writing_cards = writing_cards.count { |card| card.at_css(".post-card__title > a[href]") }
    unless writing_cards.any? && linked_writing_cards == writing_cards.length
      failures << "writing index: every list item must have one native title link"
    end

    if failures.empty? && card_count.positive?
      v.ok "#{card_count} cards use native title links with clear affordances"
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
  # Anchored to the start of the line, so prose *about* a selector cannot be
  # mistaken for the selector. Writing `:root[data-theme="light"]` inside the
  # dark block's comment put light_i above dark_i, inverted the dark range, and
  # silently halved the audit from 70 pairs to 35 — a gate that quietly checks
  # less is worse than one that fails.
  selector = ->(theme) { /^\s*:root\[data-theme="#{theme}"\]/ }
  dark_i  = lines.index { |l| l =~ selector.call("dark") }
  light_i = lines.index { |l| l =~ selector.call("light") }
  abort "tokens: could not locate the dark and light blocks" unless dark_i && light_i
  abort "tokens: dark block must precede light" unless dark_i < light_i

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

# css:deadwood is deliberately NOT in the default list yet — it currently
# reports ~230 unreachable selectors, which is a real backlog to work through,
# not a regression to block on. Add it here once it is green.
# ─────────────────────────────────────────────────────────────────────────────
# RESUME PDF
#
# Two assertions, and the second exists because the first cannot catch what
# broke here. Moving the page chrome to `onPageEnd` to fix the parse order made
# the background paint over every word: a page of perfectly extractable,
# perfectly invisible text. `rake privacy` read it happily. So did pypdf.
#
# The only thing that sees it is a rasteriser.
# ─────────────────────────────────────────────────────────────────────────────
RESUME_PDF = "assets/basant-bhattarai-resume.pdf".freeze

desc "The resume PDF must parse name-first and actually have ink on the page"
task :resume do
  abort "resume: #{RESUME_PDF} not found — run `make resume-pdf`" unless File.exist?(RESUME_PDF)
  failures = []

  # 1. Parse order. reportlab writes onPage output first, so chrome drawn there
  #    becomes line one of the document — and a parser that treats line one as
  #    the candidate name files the applicant under their own hostname.
  text = `uv run --quiet --with pypdf python -c 'import sys;from pypdf import PdfReader;print(PdfReader(sys.argv[1]).pages[0].extract_text())' #{RESUME_PDF} 2>/dev/null`
  first = text.lines.map(&:strip).reject(&:empty?).first.to_s
  if first.casecmp("BASANT BHATTARAI").zero?
    puts "  ok    first parsed line is the name"
  else
    failures << "first parsed line is #{first.inspect}, not the name"
  end

  # 2. Ink. A rasterised page with almost no dark pixels is blank, whatever the
  #    text layer says.
  if system("which pdftoppm > /dev/null 2>&1")
    Dir.mktmpdir do |dir|
      system("pdftoppm -gray -r 40 #{RESUME_PDF} #{dir}/p > /dev/null 2>&1")
      Dir["#{dir}/p*.pgm"].sort.each_with_index do |f, i|
        raw = File.binread(f)
        px = raw.split("\n", 4)[3].to_s.bytes
        ratio = px.empty? ? 0.0 : px.count { |b| b < 230 }.fdiv(px.size) * 100
        if ratio >= 3.0
          puts format("  ok    page %d has %.1f%% ink", i + 1, ratio)
        else
          failures << format("page %d is effectively blank (%.1f%% ink)", i + 1, ratio)
        end
      end
    end
  else
    puts "  skip  pdftoppm not installed — ink check skipped"
  end

  failures.each { |f| puts "  FAIL  #{f}" }
  abort "resume: #{failures.size} failure(s)" unless failures.empty?
  puts "resume: ok"
end

task default: %i[content privacy check verify jsonld tokens css:literals css:budget resume]

# ─────────────────────────────────────────────────────────────────────────────
# CSS HYGIENE
#
# `rake tokens` proves the token matrix is sound. It cannot prove the
# stylesheet actually uses it — a hardcoded hex is invisible to a token audit
# no matter what surface it lands on. Three shipped AA failures came from
# exactly that gap: a `.writing-find` block that kept a dark-only palette while
# rendering on paper gave the ⌘K hint 1.85:1 and the search field's focus ring
# 1.82:1, and a stray `#737e89` gave `.article-facts dt` 3.96:1.
#
# These three tasks close the gap from the other side, and unlike a screenshot
# diff they are platform-independent, so they belong in CI.
# ─────────────────────────────────────────────────────────────────────────────
CSS_BUILT = "_site/assets/css/site.css".freeze

# Where a raw colour is the correct answer.
LITERAL_EXEMPT = {
  "_sass/_tokens.scss"  => "literals are the point — this is where colour is defined",
  "_sass/_print.scss"   => "paper is one fixed surface; the print palette is deliberately absolute",
  "_sass/_syntax.scss"  => "Rouge token colours are defined here and audited by SCOPED_PAIRS"
}.freeze

# A mask stop carries alpha, not colour — `#000` there has no visual meaning.
LITERAL_OK_LINE = /mask-image|mask:/.freeze

desc "No raw colour literals in the component layer — everything through tokens"
task :"css:literals" do
  offenders = []

  Dir["_sass/**/*.scss"].sort.each do |path|
    next if LITERAL_EXEMPT.key?(path)

    in_block_comment = false
    File.readlines(path).each_with_index do |line, i|
      # Strip comments before matching, or the explanatory prose that documents
      # a past failure ("the ⌘K hint (#a9b2bd on --surface-2) measured 1.85:1")
      # trips the gate that the fix installed.
      in_block_comment = true  if line =~ %r{/\*} && line !~ %r{\*/}
      was_comment = in_block_comment
      in_block_comment = false if line =~ %r{\*/}
      next if was_comment

      code = line.sub(%r{//.*$}, "").sub(%r{/\*.*?\*/}, "")
      next if code =~ LITERAL_OK_LINE

      hits = code.scan(/#[0-9a-fA-F]{3,8}\b|\brgba?\(\s*\d/)
      next if hits.empty?

      offenders << format("%s:%d  %s", path, i + 1, code.strip)
    end
  end

  if offenders.empty?
    exempt = LITERAL_EXEMPT.keys.length
    puts "css:literals: ok — component layer is token-only (#{exempt} documented exemption(s))"
  else
    warn "css:literals: #{offenders.length} raw colour literal(s)"
    offenders.each { |o| warn "  #{o}" }
    warn "  Use a token, or add a documented entry to LITERAL_EXEMPT."
    abort "css:literals: FAILED"
  end
end

# Ratchet this down as dead rules go; never up without saying why in the commit.
CSS_GZIP_CEILING = 25_000

desc "The built stylesheet must stay under its gzip budget"
task :"css:budget" do
  unless File.exist?(CSS_BUILT)
    puts "css:budget: SKIP — #{CSS_BUILT} not built"
    next
  end

  require "zlib"
  require "stringio"
  raw = File.binread(CSS_BUILT)
  io = StringIO.new
  Zlib::GzipWriter.wrap(io, Zlib::BEST_COMPRESSION) { |gz| gz.write(raw) }
  gzip = io.string.bytesize

  pct = (gzip * 100.0 / CSS_GZIP_CEILING).round
  line = format("css:budget: %s — %d B gzip (%d B raw), %d%% of the %d B ceiling",
                gzip <= CSS_GZIP_CEILING ? "ok" : "OVER", gzip, raw.bytesize, pct, CSS_GZIP_CEILING)

  if gzip <= CSS_GZIP_CEILING
    puts line
  else
    abort line
  end
end

# Classes that only ever exist after site.js runs, so no built HTML contains
# them. Each one is a real hook — grep site.js before adding to this list.
JS_ONLY_SELECTORS = %w[
  code-tools code-lang copy-btn sr-live table-scroll-hint
  writing-suggest__hit writing-suggest__kind writing-suggest__title
  writing-suggest__blurb is-active is-filtering is-hit is-empty
].freeze

# Selectors that cannot appear in built HTML by construction:
#   .js …            progressive-enhancement gate; the inline bootstrap in
#                    default.html adds `js` to <html> at runtime
#   [open] [hidden]  set by dialog.showModal() and the catalog filter
#   [aria-expanded]  toggled by the nav and the search combobox
DEADWOOD_RUNTIME = /(^|\s)\.js(\s|$)|\[open\]|\[hidden\]|\[aria-expanded/.freeze

# Markup a template emits only under a condition that is false today. Unlike
# dead code, these come back on their own: `.staleness` renders the moment a
# tutorial passes its one-year freshness cutoff (_layouts/post.html:26).
DEADWOOD_CONDITIONAL = %w[.staleness].freeze

# Selectors that style AUTHORED CONTENT rather than template markup. For these,
# "matches nothing today" means "nobody has written one yet" — not "dead".
#
# The distinction matters and it is not academic. `.highlight` covers the Rouge
# token classes; the corpus currently uses a subset, and deleting the rest
# breaks highlighting the first time someone writes a language that emits one.
# `.prose ol ol` and `.callout li` are the same shape: legitimate authoring
# choices that `_templates/tutorial.md` actively scaffolds.
#
# Template-driven selectors get no such benefit of the doubt. If no layout or
# include can emit `.hero-photo`, it is unreachable, full stop.
DEADWOOD_CONTENT_ROOTS = %w[
  .highlight .prose .callout .verify .checklist .footnotes .ledger__
].freeze

desc "Every selector in the built CSS must match something in the built HTML"
task :"css:deadwood" do
  unless File.exist?(CSS_BUILT)
    puts "css:deadwood: SKIP — #{CSS_BUILT} not built"
    next
  end

  docs = Dir["_site/**/*.html"].map { |f| Nokogiri::HTML5(File.read(f)) }
  abort "css:deadwood: no built HTML found" if docs.empty?

  css = File.read(CSS_BUILT)
  # Drop at-rule preludes and declaration blocks; keep the selector text.
  css = css.gsub(%r{/\*.*?\*/}m, "")
  selectors = css.scan(/(?:^|[};])\s*([^{}@;]+?)\s*\{/).flatten

  seen = {}
  selectors.each do |group|
    group.split(",").each do |sel|
      sel = sel.strip
      next if sel.empty? || sel.start_with?("%", "from", "to") || sel =~ /^\d/
      # Nokogiri has no view state: strip pseudo-classes and pseudo-elements
      # and test the structural remainder. `:hover` on a real element is fine;
      # a selector whose *element* part matches nothing is the finding.
      # Alternation is ordered longest-first on purpose. With `focus` listed
      # before `focus-visible`, `.btn--primary:focus-visible` strips to
      # `.btn--primary-visible`, matches nothing, and gets reported as dead —
      # which is how this task first "found" eight live selectors.
      probe = sel.gsub(/::[a-z-]+(\([^)]*\))?/, "")
                 .gsub(/:(focus-within|focus-visible|first-of-type|last-of-type|only-child|first-child|last-child|nth-child\([^)]*\)|nth-of-type\([^)]*\)|not\([^)]*\)|where\([^)]*\)|has\([^)]*\)|is\([^)]*\)|disabled|checked|visited|active|target|empty|hover|focus)/, "")
                 .strip
      next if probe.empty? || probe == "*"
      # Bare element selectors (`h5`, `hr`, `video`, `textarea`, `select`) come
      # from _reset.scss and _prose.scss. They are the base layer: absent today
      # only because nobody has authored that element yet, exactly like the
      # content roots below. A stylesheet that styles `h5` only once an `h5`
      # exists is not a stylesheet.
      next unless probe =~ /[.#\[]/
      next if JS_ONLY_SELECTORS.any? { |c| probe.include?(c) }
      next if DEADWOOD_CONTENT_ROOTS.any? { |r| probe.start_with?(r) }
      next if DEADWOOD_CONDITIONAL.any? { |r| probe.start_with?(r) }
      next if probe =~ DEADWOOD_RUNTIME
      seen[probe] ||= sel
    end
  end

  dead = seen.reject do |probe, _|
    docs.any? do |doc|
      begin
        doc.at_css(probe)
      rescue StandardError
        true # a selector Nokogiri cannot parse is not evidence of death
      end
    end
  end

  if dead.empty?
    puts "css:deadwood: ok — all #{seen.length} selector(s) match rendered markup"
  else
    warn "css:deadwood: #{dead.length} of #{seen.length} selector(s) match nothing in #{docs.length} built pages"
    dead.values.sort.first(60).each { |s| warn "  #{s}" }
    warn "  ... and #{dead.length - 60} more" if dead.length > 60
    abort "css:deadwood: FAILED"
  end
end
