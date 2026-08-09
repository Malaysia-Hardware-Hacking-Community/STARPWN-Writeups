An unknown aggressor satellite has been detected in a higher orbit and is threatening critical space infrastructure. Your mission: calculate a Hohmann transfer to intercept it.

Connect to the provided shell. You will be told your circular orbit altitude, the target's circular orbit altitude, and the current phase angle between you and the target. You'll need to submit two numbers per line, space-separated:

	delta_v_burn  wait_time

	delta_v_burn  — Δv for the first (injection) burn, in m/s.
	wait_time     — seconds to wait before executing the burn so the
									target arrives at the rendezvous point at the same
									time you do.

Grading tolerances: ±10 m/s on Δv, ±60 s on wait time. You'll have five attempts per connection. Reconnect to retry with a fresh scenario.
