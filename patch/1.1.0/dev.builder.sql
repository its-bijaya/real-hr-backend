-- Affected dev release branch report-builder
-- Production servers are not affected

-- Remove previous implementation fo Builder tables
-- New tables are reflected in migrations
-- STEPS
-- ./manage.py migrate --fake builder zero
-- then , drop the tables
-- push the latest migrations and code
-- ./manage.py migrate builder

DROP TABLE IF EXISTS
  builder_report,
  builder_reportdisplayfield,
  builder_reportfilterfield,
  builder_reportfilter
  CASCADE