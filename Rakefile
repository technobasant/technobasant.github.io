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
require "shellwords"

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

  # Assets this task's owner generated — these must always be present.
  {
    "assets/apple-touch-icon.png" => 180,
    "assets/og/og-default.png" => nil
  }.each_key do |asset|
    built = File.join(SITE_DIR, asset)
    v.with(built, label: "#{asset} shipped to _site") do
      v.ok "#{asset} shipped to _site (#{File.size(built)} B)"
    end
  end

  v.report!
end

task default: %i[check verify jsonld]
