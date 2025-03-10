"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface Company {
  id: number
  name: string
  industry: string
  website: string
  description: string
  created_at: string
}

interface Contact {
  id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  position: string
  company_id: number
  created_at: string
}

interface Deal {
  id: number
  title: string
  stage: string
  value: number
  company_id: number
  contact_id: number
  description: string
  created_at: string
}

interface Interaction {
  id: number
  type: string
  summary: string
  contact_id: number | null
  deal_id: number | null
  created_at: string
  ai_analysis: string
}

interface StructuredAnalysis {
  company_name?: string
  contact_first_name?: string
  contact_last_name?: string
  deal_value?: string
  deal_stage?: string
  OverallSentiment?: string
  KeyConcernsOrObjectionsRaised?: string[]
  LevelOfInterest?: string
  SuggestedNextSteps?: string[]
}

export default function DataPage() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [deals, setDeals] = useState<Deal[]>([])
  const [interactions, setInteractions] = useState<Interaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [
          companiesRes,
          contactsRes,
          dealsRes,
          interactionsRes
        ] = await Promise.all([
          fetch("http://localhost:8000/api/v1/crm/companies/"),
          fetch("http://localhost:8000/api/v1/crm/contacts/"),
          fetch("http://localhost:8000/api/v1/crm/deals/"),
          fetch("http://localhost:8000/api/v1/crm/interactions/")
        ])

        const companiesData = await companiesRes.json()
        const contactsData = await contactsRes.json()
        const dealsData = await dealsRes.json()
        const interactionsData = await interactionsRes.json()

        setCompanies(companiesData)
        setContacts(contactsData)
        setDeals(dealsData)
        setInteractions(interactionsData)
      } catch (error) {
        console.error("Error fetching data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const parseAnalysis = (analysisStr: string): StructuredAnalysis => {
    try {
      return JSON.parse(analysisStr)
    } catch (e) {
      console.error('Error parsing analysis:', e)
      return {}
    }
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">CRM Data</h1>

      <Tabs defaultValue="interactions" className="w-full">
        <TabsList>
          <TabsTrigger value="interactions">Interactions</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="interactions">
          <Card className="p-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Date</TableHead>
                  <TableHead className="w-[40%]">Summary</TableHead>
                  <TableHead className="w-32">Contact</TableHead>
                  <TableHead className="w-32">Company</TableHead>
                  <TableHead className="w-24">Deal Value</TableHead>
                  <TableHead className="w-24">Sentiment</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {interactions.map((interaction) => {
                  const analysis = parseAnalysis(interaction.ai_analysis)
                  return (
                    <TableRow key={interaction.id}>
                      <TableCell className="whitespace-nowrap">
                        {new Date(interaction.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="max-w-0">
                        <div className="truncate">
                          {interaction.summary}
                        </div>
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {[analysis.contact_first_name, analysis.contact_last_name]
                          .filter(Boolean)
                          .join(" ") || "-"}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {analysis.company_name || "-"}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {analysis.deal_value || "-"}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs
                          ${analysis.OverallSentiment === 'positive' ? 'bg-green-100 text-green-800' :
                            analysis.OverallSentiment === 'negative' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'}`}>
                          {analysis.OverallSentiment || "neutral"}
                        </span>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="insights">
          <Card className="p-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Date</TableHead>
                  <TableHead className="w-32">Interest Level</TableHead>
                  <TableHead className="w-[35%]">Key Concerns</TableHead>
                  <TableHead className="w-[35%]">Next Steps</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {interactions.map((interaction) => {
                  const analysis = parseAnalysis(interaction.ai_analysis)
                  return (
                    <TableRow key={interaction.id}>
                      <TableCell className="whitespace-nowrap">
                        {new Date(interaction.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs
                          ${analysis.LevelOfInterest === 'high' ? 'bg-green-100 text-green-800' :
                            analysis.LevelOfInterest === 'low' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'}`}>
                          {analysis.LevelOfInterest || "medium"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <ul className="list-disc list-inside space-y-1">
                          {analysis.KeyConcernsOrObjectionsRaised?.map((concern, i) => (
                            <li key={i} className="text-sm truncate">{concern}</li>
                          ))}
                        </ul>
                      </TableCell>
                      <TableCell>
                        <ul className="list-disc list-inside space-y-1">
                          {analysis.SuggestedNextSteps?.map((step, i) => (
                            <li key={i} className="text-sm truncate">{step}</li>
                          ))}
                        </ul>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
