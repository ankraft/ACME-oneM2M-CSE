@name functions
@description Useful functions to include
;; Hide in script catalog
@hidden	

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;
;;	Further lisp-like commands
;;

;; Return the second element of a list
(defun cadr (l)
  (car (cdr l)))

;; Return the third element of a list
(defun caddr (l)
  (car (cdr (cdr l))))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;
;;	CSE functions
;;

;; Store the original value and then update the CSE's configuration
;; Return the value
(defun set-and-store-config-value (key value)
	(	(setq _previousValue (get-config key))
		(put-storage "previousConfigs" key _previousValue)
		(set-config key value)
		(_previousValue)))

;; Restore the CSE's previous configuration
(defun restore-config-value (key)
	(if (has-storage "previousConfigs" key)
		(	(set-config key 
					    (get-storage "previousConfigs" key))
			(remove-storage "previousConfigs" key))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;
;;	oneM2M helper functions
;;

;; Return the response status
(defun get-response-status (response) 
  (car response))

;; Return the response resource
(defun get-response-resource (response) 
  (cadr response))
