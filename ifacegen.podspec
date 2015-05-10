#

Pod::Spec.new do |s|

  s.name         = "ifacegen"
  s.version      = "1.0.0"
  s.summary      = "ifacegen generates native ObjC wrappers for REST+JSON APIs"
  s.homepage     = "https://github.com/ptiz/ifacegen"
  s.license      = { :type => 'BSD' }
  s.author       = { "ptiz" => "ptiz@live.ru" }
  s.platform     = :ios, "7.0"
  s.source       = { :git => "https://github.com/ptiz/ifacegen.git", :tag => '1.0.0' }
  s.source_files  = "transport/**/*.{h,m}"
  s.public_header_files = "transport/**/*.h"
  s.resources = "generator/*.py"
  s.requires_arc = true

end
