class Gia < Formula
  desc "CLI for Governance Identity API (IGA) in PingOne Advanced Identity Cloud"
  homepage "https://github.com/pingidentity/gia"
  url "https://github.com/pingidentity/gia/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"
  license "MIT"

  # Python 3.10+ required
  depends_on "python@3.11"

  def install
    # Create a virtualenv in libexec
    venv = virtualenv_create(libexec, "python3.11")
    
    # Install dependencies
    system libexec/"bin/pip", "install", "-v", "--no-binary", ":all:",
                              "--ignore-installed",
                              buildpath
    
    # Create wrapper script
    (bin/"gia").write_env_script libexec/"bin/gia", :LANG => "en_US.UTF-8"
  end

  test do
    system "#{bin}/gia", "--version"
  end
end
