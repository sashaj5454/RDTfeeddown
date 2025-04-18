import time 
import re

def check_rdt(
	rdt:str, 
	rdtplane:str
):


	if len(rdt) != 4:
		return False, "The rdt must be exactly 4 characters long."
	print("hello")
	# Check if all characters are digits
	if not rdt.isdigit():
		return False, "The rdt must contain only numeric characters."

	# Split the string into j, k, l, and m
	j, k, l, m = [int(char) for char in rdt]

	if j == 0 and l == 0:  # the RDT can't be seen on any plane
		return False, "The rdt does not exist on any plane"
	if l+m == 0 and j !=0 and rdtplane != "x":
		return False, "The rdt does not exist on the vertical plane"
	elif j+k == 0 and l !=0 and rdtplane != "y":
		return False, "The rdt does not exist on the horizontal plane"
	elif j ==0 and rdtplane != "y":
		return False, "The rdt does not exist on the horizontal plane"
	elif l ==0 and rdtplane != "x":
		return False, "The rdt does not exist on the vertical plane"
	
	return True, ""
	
def validate_rdt_and_plane(rdt, rdt_plane):
	"""
	Validate the RDT and RDT Plane combination.
	"""
	try:
		valid, message = check_rdt(rdt, rdt_plane)
		return valid, message
	except Exception as e:
		return False, str(e)
	
def validate_knob(ldb, knob):
	"""
	Validate the knob by checking its existence in the state tracker.
	Returns a tuple: (True, knob_setting) if valid, otherwise (False, error_message).
	"""
	try:
		current_timestamp = time.time()  # Get the current timestamp
		statetracker_knob_name = f"LhcStateTracker:{re.sub('/', ':', knob)}:value"
		knob_data = ldb.get(statetracker_knob_name, current_timestamp)
		if statetracker_knob_name not in knob_data:
			return False, f"Knob '{knob}' not found in the state tracker."
		knob_setting = knob_data[statetracker_knob_name][1][0]
		return True, knob_setting
	except Exception as e:
		# Log the exception if needed, and return an error without forcing a quit.
		return False, str(e)

def validate_metas(data):
	metadatas = [
			{k: v for k, v in response.get("metadata", {}).items()
			if k not in ["beam", "ref", "knob_name"]}
			for response in data.values()
		]
	if not metadatas:
		return False, None
	# Now check that they are all equal.
	if metadatas and all(meta == metadatas[0] for meta in metadatas):
		return True, metadatas[0]
	else:
		return False, metadatas[0]
	
def validate_file_structure(data, required_metadata, log_func=None):
    required_keys = ['metadata', 'data']
    if not isinstance(data, dict):
        if log_func:
            log_func("Data is not a dictionary.")
        return False
    for key in required_keys:
        if key not in data:
            if log_func:
                log_func(f"Missing {key} in correction file.")
            return False
    metadata = data['metadata']
    for key in required_metadata:
        if key not in metadata:
            if log_func:
                log_func(f"Missing {key} in correction file metadata.")
            return False
    return True