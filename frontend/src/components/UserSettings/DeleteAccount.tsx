import {
  Button,
  Container,
  Heading,
  Text,
  useDisclosure,
} from "@chakra-ui/react"

import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  const confirmationModal = useDisclosure()

  return (
    <>
      <Container maxW="full">
        <Heading size="sm" py={4}>
          Удалить аккаунт
        </Heading>
        <Text>
          Навсегда удалить ваши данные и всё, что связано с вашей
          учетной записью.
        </Text>
        <Button variant="danger" mt={4} onClick={confirmationModal.onOpen}>
          Удалить
        </Button>
        <DeleteConfirmation
          isOpen={confirmationModal.isOpen}
          onClose={confirmationModal.onClose}
        />
      </Container>
    </>
  )
}
export default DeleteAccount
