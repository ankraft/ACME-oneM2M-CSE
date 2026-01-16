;;
;;	utGetConfig.as
;;
;;	This script returns a CSE configuration value
;;

@name GetConfig
@description Return return a CSE configuration value.
@usage GetConfig <configKey>
@uppertester
@category CSE Operation

(if (< argc 1)
  (quit-with-error "\"GetConfig\" script requires a configuration key as argument"))
(quit (get-config (argv 1)))