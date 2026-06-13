// ============================================================================
// remove_toy_seed.cypher — delete ONLY the throwaway learning nodes
// ============================================================================
//
// Early in this project we seeded a tiny generic graph (:Person / :Concept /
// :Topic) before discovering the database already held a real Bacterial
// Endotoxins Testing graph. This removes our 12 toy nodes so only the real
// domain remains. It does NOT touch :Company, :Product, :Reagent, :LAL, :rFC,
// :rCR, :CompendialMethod, :Patent, :Region, or :Bacteriophage.
//
// DETACH DELETE removes a node together with any relationships attached to it,
// so this also clears the toy KNOWS/INTERESTED_IN/CREATED/RELATED_TO edges and
// the Concept-[:PART_OF]->Topic edges. The Region-[:PART_OF]->Region edges are
// between Region nodes and are untouched.
//
// Idempotent: running it again simply matches nothing.
// ----------------------------------------------------------------------------

MATCH (n)
WHERE n:Person OR n:Concept OR n:Topic
DETACH DELETE n;
